#include "ubridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

EXPORT UNode* u_create(uint8_t type) {
    UNode* node = (UNode*)calloc(1, sizeof(UNode));
    if (!node) return NULL;
    node->type = type;
    return node;
}

EXPORT void u_int(UNode* node, int64_t val) {
    if (node) node->int_val = val;
}

EXPORT void u_float(UNode* node, double val) {
    if (node) node->float_val = val;
}

EXPORT void u_str(UNode* node, const char* val) {
    if (!node || !val) return;
    node->str_val = strdup(val);
}

EXPORT void u_array(UNode* arr_node, UNode* item_node) {
    if (!arr_node || !item_node || arr_node->type != U_ARRAY) return;
    arr_node->arr_len++;
    arr_node->arr_vals = (UNode**)realloc(arr_node->arr_vals, arr_node->arr_len * sizeof(UNode*));
    arr_node->arr_vals[arr_node->arr_len - 1] = item_node;
}

EXPORT void u_object(UNode* obj_node, const char* key, UNode* val_node) {
    if (!obj_node || !key || !val_node || obj_node->type != U_OBJECT) return;
    obj_node->obj_len++;
    obj_node->obj_keys = (char**)realloc(obj_node->obj_keys, obj_node->obj_len * sizeof(char*));
    obj_node->obj_vals = (UNode**)realloc(obj_node->obj_vals, obj_node->obj_len * sizeof(UNode*));
    
    obj_node->obj_keys[obj_node->obj_len - 1] = strdup(key);
    obj_node->obj_vals[obj_node->obj_len - 1] = val_node;
}

static uint32_t compute_hash(const char* data, size_t len) {
    uint32_t hash = 5381;
    for (size_t i = 0; i < len; i++) {
        hash = ((hash << 5) + hash) + data[i];
    }
    return hash;
}

static void u_serialize(UNode* node, char** buf, size_t* cap, size_t* len) {
    if (!node) return;
    char tmp[512];
    int written = 0;

    switch (node->type) {
        case U_NULL:
            written = snprintf(tmp, sizeof(tmp), "NIL;");
            break;
        case U_INT:
            written = snprintf(tmp, sizeof(tmp), "I:%lld;", node->int_val);
            break;
        case U_FLOAT: {
            double val = node->float_val;
            if (isnan(val)) written = snprintf(tmp, sizeof(tmp), "F:NAN;");
            else if (isinf(val)) written = snprintf(tmp, sizeof(tmp), "F:INF;");
            else written = snprintf(tmp, sizeof(tmp), "F:8:%.8f;", val);
            break;
        }
        case U_STRING:
            written = snprintf(tmp, sizeof(tmp), "S:%zu:%s;", strlen(node->str_val), node->str_val);
            break;
        case U_BOOL:
            written = snprintf(tmp, sizeof(tmp), "B:%d;", node->int_val ? 1 : 0);
            break;
        case U_ARRAY:
            written = snprintf(tmp, sizeof(tmp), "A:%zu[", node->arr_len);
            break;
        case U_OBJECT: {
            for (size_t i = 0; i < node->obj_len; i++) {
                for (size_t j = i + 1; j < node->obj_len; j++) {
                    if (strcmp(node->obj_keys[i], node->obj_keys[j]) > 0) {
                        char* tk = node->obj_keys[i]; node->obj_keys[i] = node->obj_keys[j]; node->obj_keys[j] = tk;
                        UNode* tv = node->obj_vals[i]; node->obj_vals[i] = node->obj_vals[j]; node->obj_vals[j] = tv;
                    }
                }
            }
            written = snprintf(tmp, sizeof(tmp), "O:%zu{", node->obj_len);
            break;
        }
    }

    if (*len + written >= *cap) {
        *cap *= 2;
        *buf = (char*)realloc(*buf, *cap);
    }
    strcpy(*buf + *len, tmp);
    *len += written;

    if (node->type == U_ARRAY) {
        for (size_t i = 0; i < node->arr_len; i++) {
            u_serialize(node->arr_vals[i], buf, cap, len);
            if (i < node->arr_len - 1 && (*buf)[*len - 1] == ';') {
                (*buf)[*len - 1] = '|';
            }
        }
        strcat(*buf, "]");
        *len += 1;
    } else if (node->type == U_OBJECT) {
        for (size_t i = 0; i < node->obj_len; i++) {
            size_t klen = strlen(node->obj_keys[i]);
            size_t need = klen + 16;
            if (*len + need >= *cap) { *cap += need * 2; *buf = (char*)realloc(*buf, *cap); }
            *len += snprintf(*buf + *len, *cap - *len, "K:%zu:%s->", klen, node->obj_keys[i]);
            
            u_serialize(node->obj_vals[i], buf, cap, len);
            if (i < node->obj_len - 1 && (*buf)[*len - 1] == ';') {
                (*buf)[*len - 1] = '|';
            }
        }
        strcat(*buf, "}");
        *len += 1;
    }
}

EXPORT const char* u_process(UNode* root) {
    size_t cap = 2048;
    size_t len = 0;
    char* buf = (char*)malloc(cap);
    buf[0] = '\0';
    
    u_serialize(root, &buf, &cap, &len);
    
    uint32_t verification_hash = compute_hash(buf, len);
    char checksum_tag[64];
    int check_len = snprintf(checksum_tag, sizeof(checksum_tag), "V:%08X", verification_hash);
    
    buf = (char*)realloc(buf, len + check_len + 2);
    strcat(buf, "#");
    strcat(buf, checksum_tag);
    
    return buf;
}

EXPORT void u_free(UNode* root) {
    if (!root) return;
    if (root->str_val) free(root->str_val);
    if (root->arr_vals) {
        for (size_t i = 0; i < root->arr_len; i++) u_free(root->arr_vals[i]);
        free(root->arr_vals);
    }
    if (root->obj_vals) {
        for (size_t i = 0; i < root->obj_len; i++) {
            free(root->obj_keys[i]);
            u_free(root->obj_vals[i]);
        }
        free(root->obj_keys);
        free(root->obj_vals);
    }
    free(root);
}
