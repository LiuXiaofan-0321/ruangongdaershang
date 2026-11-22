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
