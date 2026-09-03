#include "ubridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static const char B64[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static uint64_t u_network_bytes(uint64_t val) {
    uint32_t num = 1;
    if (*(char*)&num == 1) {
        return (((val & 0x00000000000000FFULL) << 56) |
                ((val & 0x000000000000FF00ULL) << 40) |
                ((val & 0x0000000000FF0000ULL) << 24) |
                ((val & 0x00000000FF000000ULL) << 8)  |
                ((val & 0x000000FF00000000ULL) >> 8)  |
                ((val & 0x0000FF0000000000ULL) >> 24) |
                ((val & 0x00FF000000000000ULL) >> 40) |
                ((val & 0xFF00000000000000ULL) >> 56));
    }
    return val;
}

EXPORT UNode* ub_create(uint8_t type) {
    UNode* node = (UNode*)calloc(1, sizeof(UNode));
    if (!node) return NULL;
    node->type = type;
    node->mem_id = (uintptr_t)node;
    return node;
}

EXPORT void ub_int(UNode* node, int64_t val) {
    if (node) {
        union { int64_t i; uint64_t u; } convert;
        convert.i = val;
        convert.u = u_network_bytes(convert.u);
        node->int_val = convert.i;
    }
}

EXPORT void ub_float(UNode* node, double val) {
    if (node) {
        // Mathematically capture and freeze fractional coordinates as hard integers
        node->float_scale_val = (int64_t)round(val * U_SCALE_FACTOR);
    }
}

EXPORT void ub_str(UNode* node, const char* val) {
    if (!node || !val) return;
    node->str_val = strdup(val);
}

EXPORT void ub_array(UNode* arr_node, UNode* item_node) {
    if (!arr_node || !item_node || arr_node->type != U_ARRAY) return;
    arr_node->arr_len++;
    arr_node->arr_vals = (UNode**)realloc(arr_node->arr_vals, arr_node->arr_len * sizeof(UNode*));
    arr_node->arr_vals[arr_node->arr_len - 1] = item_node;
}

EXPORT void ub_object(UNode* obj_node, const char* key, UNode* val_node) {
    if (!obj_node || !key || !val_node || obj_node->type != U_OBJECT) return;
    obj_node->obj_len++;
    obj_node->obj_keys = (char**)realloc(obj_node->obj_keys, obj_node->obj_len * sizeof(char*));
    obj_node->obj_vals = (UNode**)realloc(obj_node->obj_vals, obj_node->obj_len * sizeof(UNode*));
    obj_node->obj_keys[obj_node->obj_len - 1] = strdup(key);
    obj_node->obj_vals[obj_node->obj_len - 1] = val_node;
}

static char* u_pack(const char* input, size_t len) {
    size_t out_len = 4 * ((len + 2) / 3);
    char* res = (char*)malloc(out_len + 1);
    size_t i = 0, j = 0;
    while (i < len) {
        uint32_t octet_a = i < len ? (unsigned char)input[i++] : 0;
        uint32_t octet_b = i < len ? (unsigned char)input[i++] : 0;
        uint32_t octet_c = i < len ? (unsigned char)input[i++] : 0;
        uint32_t triple = (octet_a << 16) + (octet_b << 8) + octet_c;
        res[j++] = B64[(triple >> 18) & 0x3F];
        res[j++] = B64[(triple >> 12) & 0x3F];
        res[j++] = (i > len + 1) ? '=' : B64[(triple >> 6) & 0x3F];
        res[j++] = (i > len) ? '=' : B64[triple & 0x3F];
    }
    res[out_len] = '\0';
    return res;
}

static uint32_t compute_fnv1a(const char* data, size_t len) {
    uint32_t hash = 2166136261U;
    for (size_t i = 0; i < len; i++) {
        hash ^= (unsigned char)data[i];
        hash *= 16777619;
    }
    return hash;
}

static void u_serialize(UNode* node, char** buf, size_t* cap, size_t* len, uintptr_t* history, size_t depth) {
    if (!node) return;
    char tmp[512] = {0};
    int written = 0;

    for (size_t i = 0; i < depth; i++) {
        if (history[i] == node->mem_id) {
            written = snprintf(tmp, sizeof(tmp), "LOOP:%p;", (void*)node->mem_id);
            if (*len + written >= *cap) { *cap *= 2; *buf = (char*)realloc(*buf, *cap); }
            strcpy(*buf + *len, tmp); *len += written;
            return;
        }
    }
    history[depth] = node->mem_id;

    switch (node->type) {
        case U_NULL:   written = snprintf(tmp, sizeof(tmp), "NIL;"); break;
        case U_INT: {
            union { int64_t i; uint64_t u; } convert;
            convert.i = node->int_val;
            convert.u = u_network_bytes(convert.u);
            written = snprintf(tmp, sizeof(tmp), "I:%lld;", (long long)convert.i); 
            break;
        }
        case U_FLOAT: {
            // Re-render floating point string output by unpacking the integer scale factor safely
            long long int_part = (long long)(node->float_scale_val / U_SCALE_FACTOR);
            long long frac_part = (long long)(llabs(node->float_scale_val) % U_SCALE_FACTOR);
            written = snprintf(tmp, sizeof(tmp), "F:8:%lld.%08lld;", int_part, frac_part);
            break;
        }
        case U_STRING: {
            char* packed_str = u_pack(node->str_val, strlen(node->str_val));
            written = snprintf(tmp, sizeof(tmp), "P:%zu:%s;", strlen(packed_str), packed_str);
            free(packed_str);
            break;
        }
        case U_BOOL:   written = snprintf(tmp, sizeof(tmp), "B:%d;", node->int_val ? 1 : 0); break;
        case U_ARRAY:  written = snprintf(tmp, sizeof(tmp), "A:%zu[", node->arr_len); break;
        case U_OBJECT: written = snprintf(tmp, sizeof(tmp), "O:%zu{", node->obj_len); break;
    }

    if (node->type == U_OBJECT) {
        for (size_t i = 0; i < node->obj_len; i++) {
            for (size_t j = i + 1; j < node->obj_len; j++) {
                if (strcmp(node->obj_keys[i], node->obj_keys[j]) > 0) {
                    char* tk = node->obj_keys[i]; node->obj_keys[i] = node->obj_keys[j]; node->obj_keys[j] = tk;
                    UNode* tv = node->obj_vals[i]; node->obj_vals[i] = node->obj_vals[j]; node->obj_vals[j] = tv;
                }
            }
        }
    }

    if (*len + written >= *cap) { *cap *= 2; *buf = (char*)realloc(*buf, *cap); }
    strcpy(*buf + *len, tmp); *len += written;

    if (node->type == U_ARRAY) {
        for (size_t i = 0; i < node->arr_len; i++) {
            u_serialize(node->arr_vals[i], buf, cap, len, history, depth + 1);
            if (i < node->arr_len - 1 && (*buf)[*len - 1] == ';') (*buf)[*len - 1] = '|';
        }
        strcat(*buf, "]"); *len += 1;
    } else if (node->type == U_OBJECT) {
        for (size_t i = 0; i < node->obj_len; i++) {
            size_t klen = strlen(node->obj_keys[i]);
            size_t need = klen + 16;
            if (*len + need >= *cap) { *cap += need * 2; *buf = (char*)realloc(*buf, *cap); }
            *len += snprintf(*buf + *len, *cap - *len, "K:%zu:%s->", klen, node->obj_keys[i]);
            u_serialize(node->obj_vals[i], buf, cap, len, history, depth + 1);
            if (i < node->obj_len - 1 && (*buf)[*len - 1] == ';') (*buf)[*len - 1] = '|';
        }
        strcat(*buf, "}"); *len += 1;
    }
}

EXPORT const char* ub_process(UNode* root) {
    size_t cap = 2048;
    size_t len = 0;
    char* buf = (char*)malloc(cap);
    buf[0] = '\0';
    
    uintptr_t* history = (uintptr_t*)calloc(1024, sizeof(uintptr_t));
    u_serialize(root, &buf, &cap, &len, history, 0);
    free(history);
    
    uint32_t signature = compute_fnv1a(buf, len);
    char crypto_tag[64] = {0};
    int crypt_len = snprintf(crypto_tag, sizeof(crypto_tag), "SIG:%08X", signature);
    
    buf = (char*)realloc(buf, len + crypt_len + 2);
    strcat(buf, "#");
    strcat(buf, crypto_tag);
    
    return buf;
}

static void u_free_tracked(UNode* root, uintptr_t* freed_history, size_t* count) {
    if (!root) return;
    for (size_t i = 0; i < *count; i++) {
        if (freed_history[i] == root->mem_id) return;
    }
    freed_history[(*count)++] = root->mem_id;

    if (root->str_val) free(root->str_val);
    if (root->arr_vals) {
        for (size_t i = 0; i < root->arr_len; i++) {
            u_free_tracked(root->arr_vals[i], freed_history, count);
        }
        free(root->arr_vals);
    }
    if (root->obj_vals) {
        for (size_t i = 0; i < root->obj_len; i++) {
            free(root->obj_keys[i]);
            u_free_tracked(root->obj_vals[i], freed_history, count);
        }
        free(root->obj_keys);
        free(root->obj_vals);
    }
    free(root);
}

EXPORT void ub_free(UNode* root) {
    uintptr_t* freed_history = (uintptr_t*)calloc(2048, sizeof(uintptr_t));
    size_t count = 0;
    u_free_tracked(root, freed_history, &count);
    free(freed_history);
}

EXPORT void ub_string_free(char* ptr) {
    if (ptr) free(ptr); // Destroys the leak trace vector created during u_process pipelines
}
