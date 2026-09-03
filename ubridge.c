#include "ubridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

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
    if (!node) return;
    union { int64_t i; uint64_t u; } convert;
    convert.i = val;
    convert.u = u_network_bytes(convert.u);
    node->int_val = convert.i;
}

EXPORT void ub_float(UNode* node, double val) {
    if (node) node->float_scale_val = (int64_t)round(val * U_SCALE_FACTOR);
}

EXPORT void ub_str(UNode* node, const char* val) {
    if (!node || !val) return;
    char* new_str = strdup(val);
    if (!new_str) return;
    free(node->str_val);
    node->str_val = new_str;
}

EXPORT void ub_array(UNode* arr_node, UNode* item_node) {
    if (!arr_node || !item_node || arr_node->type != U_ARRAY) return;
    size_t next_len = arr_node->arr_len + 1;
    struct UNode** checked_mem = (struct UNode**)realloc(arr_node->arr_vals, next_len * sizeof(UNode*));
    if (!checked_mem) return; // Fail-safe realloc protection
    arr_node->arr_vals = checked_mem;
    arr_node->arr_vals[arr_node->arr_len] = item_node;
    arr_node->arr_len = next_len;
}

EXPORT void ub_object(UNode* obj_node, const char* key, UNode* val_node) {
    if (!obj_node || !key || !val_node || obj_node->type != U_OBJECT) return;
    size_t next_len = obj_node->obj_len + 1;
    char** checked_keys = (char**)realloc(obj_node->obj_keys, next_len * sizeof(char*));
    if (!checked_keys) return;
    obj_node->obj_keys = checked_keys;

    struct UNode** checked_vals = (struct UNode**)realloc(obj_node->obj_vals, next_len * sizeof(UNode*));
    if (!checked_vals) return;
    obj_node->obj_vals = checked_vals;

    obj_node->obj_keys[obj_node->obj_len] = strdup(key);
    obj_node->obj_vals[obj_node->obj_len] = val_node;
    obj_node->obj_len = next_len;
}

static char* u_pack(const char* input, size_t len) {
    size_t out_len = 4 * ((len + 2) / 3);
    char* res = (char*)malloc(out_len + 1);
    if (!res) return NULL;
    size_t i = 0, j = 0;
    while (i < len) {
        size_t remaining = len - i;
        uint32_t octet_a = (unsigned char)input[i++];
        uint32_t octet_b = remaining > 1 ? (unsigned char)input[i++] : 0;
        uint32_t octet_c = remaining > 2 ? (unsigned char)input[i++] : 0;
        uint32_t triple = (octet_a << 16) + (octet_b << 8) + octet_c;
        res[j++] = B64[(triple >> 18) & 0x3F];
        res[j++] = B64[(triple >> 12) & 0x3F];
        res[j++] = remaining > 1 ? B64[(triple >> 6) & 0x3F] : '=';
        res[j++] = remaining > 2 ? B64[triple & 0x3F] : '=';
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

static void u_serialize(UNode* node, char** buf, size_t* cap, size_t* len, uintptr_t** history, size_t* hist_cap, size_t depth) {
    if (!node) return;
    char tmp[128] = {0};
    int written = 0;

    for (size_t i = 0; i < depth; i++) {
        if ((*history)[i] == node->mem_id) {
            written = snprintf(tmp, sizeof(tmp), "LOOP:%p;", (void*)node->mem_id);
            if (*len + written >= *cap) { *cap *= 2; *buf = (char*)realloc(*buf, *cap); }
            strcpy(*buf + *len, tmp); *len += written;
            return;
        }
    }

    if (depth >= *hist_cap) {
        *hist_cap *= 2;
        uintptr_t* checked_hist = (uintptr_t*)realloc(*history, *hist_cap * sizeof(uintptr_t));
        if (!checked_hist) return;
        *history = checked_hist;
    }
    (*history)[depth] = node->mem_id;

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
            long long int_part = (long long)(llabs(node->float_scale_val) / U_SCALE_FACTOR);
            long long frac_part = (long long)(llabs(node->float_scale_val) % U_SCALE_FACTOR);
            if (node->float_scale_val < 0) {
                written = snprintf(tmp, sizeof(tmp), "F:8:-%lld.%08lld;", int_part, frac_part);
            } else {
                written = snprintf(tmp, sizeof(tmp), "F:8:%lld.%08lld;", int_part, frac_part);
            }
            break;
        }
        case U_STRING: {
            char* packed_str = u_pack(node->str_val, strlen(node->str_val));
            if (packed_str) {
                size_t packed_len = strlen(packed_str);
                size_t header_len = (size_t)snprintf(tmp, sizeof(tmp), "P:%zu:", packed_len);
                size_t required = header_len + packed_len + 1;

                if (*len + required >= *cap) {
                    size_t new_cap = *cap;
                    while (*len + required >= new_cap) {
                        new_cap *= 2;
                    }
                    char* checked_buf = (char*)realloc(*buf, new_cap);
                    if (!checked_buf) {
                        free(packed_str);
                        return;
                    }
                    *buf = checked_buf;
                    *cap = new_cap;
                }

                memcpy(*buf + *len, tmp, header_len);
                *len += header_len;

                memcpy(*buf + *len, packed_str, packed_len);
                *len += packed_len;

                (*buf)[(*len)++] = ';';
                (*buf)[*len] = '\0';

                free(packed_str);
                return;
            }
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
            u_serialize(node->arr_vals[i], buf, cap, len, history, hist_cap, depth + 1);
            if (i < node->arr_len - 1 && (*buf)[*len - 1] == ';') (*buf)[*len - 1] = '|';
        }
        strcat(*buf, "]"); *len += 1;
    } else if (node->type == U_OBJECT) {
        for (size_t i = 0; i < node->obj_len; i++) {
            size_t klen = strlen(node->obj_keys[i]);
            size_t need = klen + 32;
            if (*len + need >= *cap) { *cap += need * 2; *buf = (char*)realloc(*buf, *cap); }
            *len += snprintf(*buf + *len, *cap - *len, "K:%zu:%s->", klen, node->obj_keys[i]);
            u_serialize(node->obj_vals[i], buf, cap, len, history, hist_cap, depth + 1);
            if (i < node->obj_len - 1 && (*buf)[*len - 1] == ';') (*buf)[*len - 1] = '|';
        }
        strcat(*buf, "}"); *len += 1;
    }
}

EXPORT const char* ub_process(UNode* root) {
    size_t cap = 2048;
    size_t len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) return NULL;
    buf[0] = '\0';
    
    size_t hist_cap = 256;
    uintptr_t* history = (uintptr_t*)malloc(hist_cap * sizeof(uintptr_t));
    if (!history) { free(buf); return NULL; }
    
    u_serialize(root, &buf, &cap, &len, &history, &hist_cap, 0);
    free(history);
    
    uint32_t signature = compute_fnv1a(buf, len);
    char crypto_tag[32] = {0};
    int crypt_len = snprintf(crypto_tag, sizeof(crypto_tag), "SIG:%08X", signature);
    
    buf = (char*)realloc(buf, len + crypt_len + 2);
    strcat(buf, "#");
    strcat(buf, crypto_tag);
    
    return buf;
}

static void u_free_tracked(UNode* root, uintptr_t** freed_history, size_t* cap, size_t* count) {
    if (!root) return;

    uintptr_t root_id = (uintptr_t)root;

    for (size_t i = 0; i < *count; i++) {
        if ((*freed_history)[i] == root_id) return;
    }

    if (*count >= *cap) {
        *cap *= 2;
        uintptr_t* checked_freed = (uintptr_t*)realloc(*freed_history, *cap * sizeof(uintptr_t));
        if (!checked_freed) return;
        *freed_history = checked_freed;
    }

    (*freed_history)[(*count)++] = root_id;

    if (root->str_val) free(root->str_val);
    if (root->arr_vals) {
        for (size_t i = 0; i < root->arr_len; i++) {
            u_free_tracked(root->arr_vals[i], freed_history, cap, count);
        }
        free(root->arr_vals);
    }
    if (root->obj_vals) {
        for (size_t i = 0; i < root->obj_len; i++) {
            free(root->obj_keys[i]);
            u_free_tracked(root->obj_vals[i], freed_history, cap, count);
        }
        free(root->obj_keys);
        free(root->obj_vals);
    }
    free(root);
}

EXPORT void ub_free(UNode* root) {
    size_t cap = 256;
    uintptr_t* freed_history = (uintptr_t*)malloc(cap * sizeof(uintptr_t));
    if (!freed_history) return;
    size_t count = 0;
    u_free_tracked(root, &freed_history, &cap, &count);
    free(freed_history);
}

EXPORT void ub_string_free(char* ptr) {
    if (ptr) free(ptr);
}
