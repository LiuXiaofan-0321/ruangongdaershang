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
