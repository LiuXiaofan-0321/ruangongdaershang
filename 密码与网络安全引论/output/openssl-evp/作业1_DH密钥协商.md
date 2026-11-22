# 作业 1 · Diffie-Hellman 密钥协商

**实测结论**　Alice 和 Bob 得到的共享秘密均为 256 字节，长度和内容一致。

## 实现步骤

1. 使用 OpenSSL 内置的 `ffdhe2048` 参数组，两次调用 `EVP_PKEY_keygen`，分别生成 Alice 和 Bob 的密钥对。
2. 使用 `i2d_PUBKEY` 和 `d2i_PUBKEY` 模拟公钥发送与接收。双方将私钥保留在各自的密钥对象中。
3. 两方各自初始化派生上下文，用 `EVP_PKEY_derive_set_peer` 设置对方的公钥，再用 `EVP_PKEY_derive` 计算共享秘密。开启 DH 前导零填充，将输出固定为 256 字节。
4. 先比较长度，再用 `CRYPTO_memcmp` 比较内容。结束时清除共享秘密缓冲区并释放密钥和上下文。

## 编译与运行

配有 GCC 和 OpenSSL 3.x 开发文件时，在源码所在目录运行。

```powershell
gcc -std=c11 -Wall -Wextra dh_ffdhe2048.c -o dh_ffdhe2048.exe -lcrypto
./dh_ffdhe2048.exe
```

## 实测输出

运行环境为 Windows、GCC 16.2.0 和 OpenSSL 3.5.7。程序退出码为 0。

```text
DH group: ffdhe2048
Alice shared secret: 256 bytes
Bob shared secret:   256 bytes
Secret lengths match: YES
Shared secrets match: YES
```

官方文档　[OpenSSL 的 DH 参数组](https://docs.openssl.org/3.5/man7/EVP_PKEY-DH/) · [EVP 密钥派生](https://docs.openssl.org/3.5/man3/EVP_PKEY_derive/)

## 完整 C 源码

```c
#include <stdio.h>
#include <stdlib.h>
#include <openssl/crypto.h>
#include <openssl/dh.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/x509.h>

enum { SECRET_BYTES = 2048 / 8 };
static const char group[] = "ffdhe2048";

static EVP_PKEY *generate_key(void)
{
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_from_name(NULL, "DH", NULL);
    EVP_PKEY *key = NULL;

    if (ctx == NULL || EVP_PKEY_keygen_init(ctx) <= 0 ||
        EVP_PKEY_CTX_set_group_name(ctx, group) <= 0 ||
        EVP_PKEY_keygen(ctx, &key) <= 0) {
        EVP_PKEY_free(key);
        key = NULL;
    }
    EVP_PKEY_CTX_free(ctx);
    return key;
}

/* Round-trip the public key through DER to simulate transmission. */
static EVP_PKEY *exchange_public_key(const EVP_PKEY *key)
{
    unsigned char *der = NULL;
    int der_len = i2d_PUBKEY(key, &der);
    const unsigned char *cursor = der;
    EVP_PKEY *public_key = NULL;

    if (der_len > 0)
        public_key = d2i_PUBKEY(NULL, &cursor, der_len);
    OPENSSL_free(der);
    return public_key;
}

static int derive_secret(EVP_PKEY *own_key, EVP_PKEY *peer_public_key,
                         unsigned char *secret, size_t *secret_len)
{
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_from_pkey(NULL, own_key, NULL);
    int ok = ctx != NULL &&
             EVP_PKEY_derive_init(ctx) > 0 &&
             EVP_PKEY_derive_set_peer(ctx, peer_public_key) > 0 &&
             EVP_PKEY_CTX_set_dh_pad(ctx, 1) > 0 &&
             EVP_PKEY_derive(ctx, secret, secret_len) > 0;

    EVP_PKEY_CTX_free(ctx);
    return ok;
}

int main(void)
{
    EVP_PKEY *alice = NULL, *bob = NULL;
    EVP_PKEY *alice_public = NULL, *bob_public = NULL;
    unsigned char alice_secret[SECRET_BYTES], bob_secret[SECRET_BYTES];
    size_t alice_len = sizeof alice_secret, bob_len = sizeof bob_secret;
    int status = EXIT_FAILURE;

    alice = generate_key();
    bob = generate_key();
    if (alice == NULL || bob == NULL)
        goto cleanup;

    alice_public = exchange_public_key(alice);
    bob_public = exchange_public_key(bob);
    if (alice_public == NULL || bob_public == NULL)
        goto cleanup;

    if (!derive_secret(alice, bob_public, alice_secret, &alice_len) ||
        !derive_secret(bob, alice_public, bob_secret, &bob_len))
        goto cleanup;

    int same_length = alice_len == bob_len;
    int same = same_length &&
               CRYPTO_memcmp(alice_secret, bob_secret, alice_len) == 0;
    printf("DH group: %s\n", group);
    printf("Alice shared secret: %zu bytes\n", alice_len);
    printf("Bob shared secret:   %zu bytes\n", bob_len);
    printf("Secret lengths match: %s\n", same_length ? "YES" : "NO");
    printf("Shared secrets match: %s\n", same ? "YES" : "NO");
    status = same ? EXIT_SUCCESS : EXIT_FAILURE;

cleanup:
    if (status != EXIT_SUCCESS) {
        unsigned long error = ERR_get_error();
        if (error != 0)
            fprintf(stderr, "DH error: %s\n", ERR_error_string(error, NULL));
    }
    OPENSSL_cleanse(alice_secret, sizeof alice_secret);
    OPENSSL_cleanse(bob_secret, sizeof bob_secret);
    EVP_PKEY_free(alice_public);
    EVP_PKEY_free(bob_public);
    EVP_PKEY_free(alice);
    EVP_PKEY_free(bob);
    return status;
}
```
