# 作业 2 · AES-128-CBC 加密与解密

**实测结论**　加密得到 48 字节密文，解密后恢复 35 字节原通知，长度和内容一致。

## 实现步骤

1. 两次调用 `RAND_bytes`，分别生成 16 字节密钥和 16 字节初始向量（IV）。
2. 依次调用 `EVP_EncryptInit_ex`、`EVP_EncryptUpdate` 和 `EVP_EncryptFinal_ex` 加密，每行以十六进制输出一个密文分组。
3. 用同一密钥和 IV 调用 `EVP_DecryptInit_ex`、`EVP_DecryptUpdate` 和 `EVP_DecryptFinal_ex` 解密。
4. 先比较长度，再用 `memcmp` 比较内容。检查函数返回值，退出前释放上下文并清除密钥。

## 编译与运行

配有 GCC 和 OpenSSL 3.x 开发文件时，在源码所在目录运行。

```powershell
gcc -std=c11 -Wall -Wextra aes_128_cbc.c -o aes_128_cbc.exe -lcrypto
./aes_128_cbc.exe
```

## 实测输出

运行环境为 Windows、GCC 16.2.0 和 OpenSSL 3.5.7。程序退出码为 0。

```text
Original (35 bytes): Class meeting at 18:30 in Room 301.
Ciphertext (48 bytes, hex):
2375f1b4c3c4b8ce0a8c4899e72a9599
43adb722aa6cddd86b4a8ac55d8d6423
f8e2acbd91b46feeb5ddb7a344e8e6da
Decrypted (35 bytes): Class meeting at 18:30 in Room 301.
Plaintext lengths match: YES
Plaintexts match: YES
```

AES 的分组大小为 16 字节。EVP 默认填充给 35 字节明文补 13 字节，因此密文为 3 个分组。每次运行都会重新生成密钥和 IV，密文通常随之变化。

官方文档　[OpenSSL EVP 加解密](https://docs.openssl.org/3.5/man3/EVP_EncryptInit/) · [随机字节生成](https://docs.openssl.org/3.5/man3/RAND_bytes/)

## 完整 C 源码

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/crypto.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/rand.h>

static void print_hex(const unsigned char *data, int length)
{
    for (int i = 0; i < length; ++i) {
        printf("%02x", (unsigned int)data[i]);
        if ((i + 1) % 16 == 0 || i + 1 == length)
            putchar('\n');
    }
}

int main(void)
{
    const unsigned char message[] = "Class meeting at 18:30 in Room 301.";
    const int message_len = (int)(sizeof message - 1);
    unsigned char key[16], iv[16];
    unsigned char ciphertext[sizeof message + EVP_MAX_BLOCK_LENGTH];
    unsigned char recovered[sizeof ciphertext + EVP_MAX_BLOCK_LENGTH];
    EVP_CIPHER_CTX *enc = NULL, *dec = NULL;
    int part_len = 0, ciphertext_len = 0, recovered_len = 0;
    int status = EXIT_FAILURE;

    if (RAND_bytes(key, sizeof key) != 1 || RAND_bytes(iv, sizeof iv) != 1)
        goto cleanup;
    enc = EVP_CIPHER_CTX_new();
    dec = EVP_CIPHER_CTX_new();
    if (enc == NULL || dec == NULL)
        goto cleanup;

    if (EVP_EncryptInit_ex(enc, EVP_aes_128_cbc(), NULL, key, iv) != 1 ||
        EVP_EncryptUpdate(enc, ciphertext, &part_len,
                          message, message_len) != 1)
        goto cleanup;
    ciphertext_len = part_len;
    if (EVP_EncryptFinal_ex(enc, ciphertext + ciphertext_len, &part_len) != 1)
        goto cleanup;
    ciphertext_len += part_len;

    if (EVP_DecryptInit_ex(dec, EVP_aes_128_cbc(), NULL, key, iv) != 1 ||
        EVP_DecryptUpdate(dec, recovered, &part_len,
                          ciphertext, ciphertext_len) != 1)
        goto cleanup;
    recovered_len = part_len;
    if (EVP_DecryptFinal_ex(dec, recovered + recovered_len, &part_len) != 1)
        goto cleanup;
    recovered_len += part_len;

    int same_length = recovered_len == message_len;
    int same = same_length &&
               memcmp(message, recovered, (size_t)message_len) == 0;
    printf("Original (%d bytes): %s\n", message_len, (const char *)message);
    printf("Ciphertext (%d bytes, hex):\n", ciphertext_len);
    print_hex(ciphertext, ciphertext_len);
    printf("Decrypted (%d bytes): %.*s\n", recovered_len, recovered_len,
           (const char *)recovered);
    printf("Plaintext lengths match: %s\n", same_length ? "YES" : "NO");
    printf("Plaintexts match: %s\n", same ? "YES" : "NO");
    status = same ? EXIT_SUCCESS : EXIT_FAILURE;

cleanup:
    if (status != EXIT_SUCCESS) {
        unsigned long error = ERR_get_error();
        if (error != 0)
            fprintf(stderr, "AES error: %s\n", ERR_error_string(error, NULL));
    }
    EVP_CIPHER_CTX_free(enc);
    EVP_CIPHER_CTX_free(dec);
    OPENSSL_cleanse(key, sizeof key);
    return status;
}
```
