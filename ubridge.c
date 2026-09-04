#include "ubridge.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <stdarg.h>

static const char B64[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789+/";

/* ============================================================
 * SAFE STRING DUPLICATION
 * ============================================================ */

static char* u_strdup(const char* s)
{
    size_t len;
    char* p;

    if (!s) {
        return NULL;
    }

    len = strlen(s);

    if (len == SIZE_MAX) {
        return NULL;
    }

    p = (char*)malloc(len + 1);

    if (!p) {
        return NULL;
    }

    memcpy(p, s, len + 1);

    return p;
}

/* ============================================================
 * DYNAMIC OUTPUT BUFFER
 * ============================================================ */

static int ensure_buf_cap(
    char** buf,
    size_t* cap,
    size_t len,
    size_t needed
)
{
    size_t required;
    size_t new_cap;
    char* new_buf;

    if (!buf || !*buf || !cap) {
        return 0;
    }

    if (needed > SIZE_MAX - len - 1) {
        return 0;
    }

    required = len + needed + 1;

    if (required <= *cap) {
        return 1;
    }

    new_cap = (*cap > 0) ? *cap : 256;

    while (new_cap < required) {
        if (new_cap > SIZE_MAX / 2) {
            new_cap = required;
            break;
        }

        new_cap *= 2;
    }

    if (new_cap < required) {
        return 0;
    }

    new_buf = (char*)realloc(
        *buf,
        new_cap
    );

    if (!new_buf) {
        return 0;
    }

    *buf = new_buf;
    *cap = new_cap;

    return 1;
}

static int append_bytes(
    char** buf,
    size_t* cap,
    size_t* len,
    const char* data,
    size_t data_len
)
{
    if (!buf || !*buf || !cap || !len) {
        return 0;
    }

    if (!data && data_len != 0) {
        return 0;
    }

    if (!ensure_buf_cap(
        buf,
        cap,
        *len,
        data_len
    )) {
        return 0;
    }

    if (data_len != 0) {
        memcpy(
            *buf + *len,
            data,
            data_len
        );
    }

    *len += data_len;

    (*buf)[*len] = '\0';

    return 1;
}

static int append_cstr(
    char** buf,
    size_t* cap,
    size_t* len,
    const char* str
)
{
    if (!str) {
        return 0;
    }

    return append_bytes(
        buf,
        cap,
        len,
        str,
        strlen(str)
    );
}

static int append_fmt(
    char** buf,
    size_t* cap,
    size_t* len,
    const char* fmt,
    ...
)
{
    va_list args;
    va_list copy;
    int required;
    int written;

    if (!buf || !*buf || !cap || !len || !fmt) {
        return 0;
    }

    va_start(args, fmt);

    va_copy(copy, args);

    required = vsnprintf(
        NULL,
        0,
        fmt,
        copy
    );

    va_end(copy);

    if (required < 0) {
        va_end(args);
        return 0;
    }

    if (!ensure_buf_cap(
        buf,
        cap,
        *len,
        (size_t)required
    )) {
        va_end(args);
        return 0;
    }

    written = vsnprintf(
        *buf + *len,
        *cap - *len,
        fmt,
        args
    );

    va_end(args);

    if (written < 0 ||
        written != required) {
        return 0;
    }

    *len += (size_t)written;

    return 1;
}

/* ============================================================
 * NODE CREATION
 * ============================================================ */

UBRIDGE_API UNode* UBRIDGE_CALL
ub_create(uint8_t type)
{
    UNode* node;

    switch (type) {
        case U_NULL:
        case U_INT:
        case U_FLOAT:
        case U_STRING:
        case U_BOOL:
        case U_ARRAY:
        case U_OBJECT:
            break;

        default:
            return NULL;
    }

    node = (UNode*)calloc(
        1,
        sizeof(UNode)
    );

    if (!node) {
        return NULL;
    }

    node->type = type;

    /*
     * Process-local identity used only for cycle detection.
     * It is NOT a wire/shared-memory identifier.
     */
    node->mem_id = (uintptr_t)node;

    node->precision_mode =
        UB_MODE_FIXED;

    node->math_hash_checkpoint =
        UINT32_C(2166136261);

    return node;
}

/* ============================================================
 * INTEGER
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_int(
    UNode* node,
    int64_t val
)
{
    if (!node) {
        return;
    }

    node->type = U_INT;

    node->int_val = val;

    node->float_scale_val = 0;

    node->scientific_coeff = 0;

    node->scientific_exp = 0;

    node->precision_mode =
        UB_MODE_FIXED;
}

/* ============================================================
 * FIXED-POINT FLOAT
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_float(
    UNode* node,
    double val
)
{
    long double scaled;
    long double rounded;

    if (!node) {
        return;
    }

    if (!isfinite(val)) {
        node->type = U_NULL;

        node->float_scale_val = 0;

        node->scientific_coeff = 0;

        node->scientific_exp = 0;

        node->precision_mode =
            UB_MODE_FIXED;

        return;
    }

    scaled =
        (long double)val *
        (long double)U_SCALE_FACTOR;

    if (scaled >
            (long double)INT64_MAX ||
        scaled <
            (long double)INT64_MIN) {

        node->type = U_NULL;

        node->float_scale_val = 0;

        node->scientific_coeff = 0;

        node->scientific_exp = 0;

        node->precision_mode =
            UB_MODE_FIXED;

        return;
    }

    rounded = roundl(scaled);

    if (rounded >
            (long double)INT64_MAX ||
        rounded <
            (long double)INT64_MIN) {

        node->type = U_NULL;

        node->float_scale_val = 0;

        node->scientific_coeff = 0;

        node->scientific_exp = 0;

        node->precision_mode =
            UB_MODE_FIXED;

        return;
    }

    node->type = U_FLOAT;

    node->precision_mode =
        UB_MODE_FIXED;

    node->float_scale_val =
        (int64_t)rounded;

    node->scientific_coeff = 0;

    node->scientific_exp = 0;
}

/* ============================================================
 * STRING
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_str(
    UNode* node,
    const char* val
)
{
    char* new_str;

    if (!node || !val) {
        return;
    }

    new_str = u_strdup(val);

    if (!new_str) {
        return;
    }

    free(node->str_val);

    node->str_val = new_str;

    node->type = U_STRING;
}

/* ============================================================
 * ARRAY
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_array(
    UNode* arr_node,
    UNode* item_node
)
{
    size_t next_len;
    size_t bytes;
    UNode** new_vals;

    if (!arr_node ||
        !item_node ||
        arr_node->type != U_ARRAY) {
        return;
    }

    if (arr_node->arr_len == SIZE_MAX) {
        return;
    }

    next_len =
        arr_node->arr_len + 1;

    if (next_len >
        SIZE_MAX / sizeof(UNode*)) {
        return;
    }

    bytes =
        next_len * sizeof(UNode*);

    new_vals =
        (UNode**)realloc(
            arr_node->arr_vals,
            bytes
        );

    if (!new_vals) {
        return;
    }

    new_vals[
        arr_node->arr_len
    ] = item_node;

    arr_node->arr_vals =
        new_vals;

    arr_node->arr_len =
        next_len;
}

/* ============================================================
 * OBJECT
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_object(
    UNode* obj_node,
    const char* key,
    UNode* val_node
)
{
    size_t next_len;
    size_t key_bytes;
    size_t value_bytes;
    char* dup_key;
    char** new_keys;
    UNode** new_vals;

    if (!obj_node ||
        !key ||
        !val_node ||
        obj_node->type != U_OBJECT) {
        return;
    }

    if (obj_node->obj_len == SIZE_MAX) {
        return;
    }

    next_len =
        obj_node->obj_len + 1;

    if (next_len >
        SIZE_MAX / sizeof(char*)) {
        return;
    }

    if (next_len >
        SIZE_MAX / sizeof(UNode*)) {
        return;
    }

    key_bytes =
        next_len * sizeof(char*);

    value_bytes =
        next_len * sizeof(UNode*);

    dup_key =
        u_strdup(key);

    if (!dup_key) {
        return;
    }

    new_keys =
        (char**)malloc(key_bytes);

    if (!new_keys) {
        free(dup_key);
        return;
    }

    new_vals =
        (UNode**)malloc(value_bytes);

    if (!new_vals) {
        free(new_keys);
        free(dup_key);
        return;
    }

    if (obj_node->obj_len != 0) {

        if (!obj_node->obj_keys ||
            !obj_node->obj_vals) {

            free(new_keys);
            free(new_vals);
            free(dup_key);

            return;
        }

        memcpy(
            new_keys,
            obj_node->obj_keys,
            obj_node->obj_len *
                sizeof(char*)
        );

        memcpy(
            new_vals,
            obj_node->obj_vals,
            obj_node->obj_len *
                sizeof(UNode*)
        );
    }

    new_keys[
        obj_node->obj_len
    ] = dup_key;

    new_vals[
        obj_node->obj_len
    ] = val_node;

    free(obj_node->obj_keys);

    free(obj_node->obj_vals);

    obj_node->obj_keys =
        new_keys;

    obj_node->obj_vals =
        new_vals;

    obj_node->obj_len =
        next_len;
}

/* ============================================================
 * BASE64
 * ============================================================ */

static char* u_pack(
    const char* input,
    size_t len
)
{
    size_t groups;
    size_t out_len;
    size_t i;
    size_t j;
    char* res;

    if (!input) {
        return NULL;
    }

    if (len >
        (SIZE_MAX - 2) / 3) {
        return NULL;
    }

    groups =
        (len + 2) / 3;

    if (groups >
        SIZE_MAX / 4) {
        return NULL;
    }

    out_len =
        groups * 4;

    if (out_len == SIZE_MAX) {
        return NULL;
    }

    res =
        (char*)malloc(
            out_len + 1
        );

    if (!res) {
        return NULL;
    }

    i = 0;
    j = 0;

    while (i < len) {

        size_t remaining =
            len - i;

        uint32_t a =
            (unsigned char)input[i++];

        uint32_t b = 0;
        uint32_t c = 0;

        if (remaining > 1) {
            b =
                (unsigned char)input[i++];
        }

        if (remaining > 2) {
            c =
                (unsigned char)input[i++];
        }

        {
            uint32_t triple =
                (a << 16) |
                (b << 8) |
                c;

            res[j++] =
                B64[
                    (triple >> 18) &
                    0x3F
                ];

            res[j++] =
                B64[
                    (triple >> 12) &
                    0x3F
                ];

            res[j++] =
                (remaining > 1)
                    ? B64[
                        (triple >> 6) &
                        0x3F
                    ]
                    : '=';

            res[j++] =
                (remaining > 2)
                    ? B64[
                        triple & 0x3F
                    ]
                    : '=';
        }
    }

    res[out_len] = '\0';

    return res;
}

/* ============================================================
 * FNV-1a CHECKSUM
 * ============================================================ */

static uint32_t compute_fnv1a(
    const char* data,
    size_t len
)
{
    uint32_t hash =
        UINT32_C(2166136261);

    size_t i;

    if (!data && len != 0) {
        return 0;
    }

    for (i = 0; i < len; ++i) {
        hash ^=
            (uint8_t)data[i];

        hash *=
            UINT32_C(16777619);
    }

    return hash;
}

/* ============================================================
 * SERIALIZATION HISTORY
 * ============================================================ */

static int history_contains(
    const uintptr_t* history,
    size_t depth,
    uintptr_t id
)
{
    size_t i;

    if (!history) {
        return 0;
    }

    for (i = 0; i < depth; ++i) {
        if (history[i] == id) {
            return 1;
        }
    }

    return 0;
}

static int history_reserve(
    uintptr_t** history,
    size_t* capacity,
    size_t required
)
{
    size_t new_cap;
    uintptr_t* p;

    if (!history || !capacity) {
        return 0;
    }

    if (required <= *capacity) {
        return 1;
    }

    new_cap =
        (*capacity > 0)
            ? *capacity
            : 16;

    while (new_cap < required) {

        if (new_cap >
            SIZE_MAX / 2) {

            new_cap =
                required;

            break;
        }

        new_cap *= 2;
    }

    if (new_cap < required ||
        new_cap >
            SIZE_MAX / sizeof(uintptr_t)) {
        return 0;
    }

    p =
        (uintptr_t*)realloc(
            *history,
            new_cap *
                sizeof(uintptr_t)
        );

    if (!p) {
        return 0;
    }

    *history = p;

    *capacity = new_cap;

    return 1;
}

/* ============================================================
 * SERIALIZER
 * ============================================================ */

static int u_serialize(
    const UNode* node,
    char** buf,
    size_t* cap,
    size_t* len,
    uintptr_t** history,
    size_t* hist_cap,
    size_t depth
)
{
    if (!node) {
        return append_cstr(
            buf,
            cap,
            len,
            "NIL;"
        );
    }

    if (depth >=
        UB_MAX_SERIALIZE_DEPTH) {
        return append_cstr(
            buf,
            cap,
            len,
            "DEPTH;"
        );
    }

    if (history_contains(
        *history,
        depth,
        node->mem_id
    )) {
        return append_cstr(
            buf,
            cap,
            len,
            "CYCLE;"
        );
    }

    if (!history_reserve(
        history,
        hist_cap,
        depth + 1
    )) {
        return 0;
    }

    (*history)[depth] =
        node->mem_id;

    switch (node->type) {

        case U_NULL:
            return append_cstr(
                buf,
                cap,
                len,
                "NIL;"
            );

        case U_INT:
            return append_fmt(
                buf,
                cap,
                len,
                "I:%lld;",
                (long long)
                    node->int_val
            );

        case U_BOOL:
            return append_fmt(
                buf,
                cap,
                len,
                "B:%d;",
                node->int_val
                    ? 1
                    : 0
            );

        case U_FLOAT:

            if (node->precision_mode ==
                UB_MODE_SCIENTIFIC) {

                return append_fmt(
                    buf,
                    cap,
                    len,
                    "S:C:%lld:E:%d;",
                    (long long)
                        node->scientific_coeff,
                    (int)
                        node->scientific_exp
                );
            }

            {
                int negative =
                    node->float_scale_val <
                    0;

                uint64_t magnitude;

                uint64_t integer_part;
                uint64_t fraction_part;

                if (negative) {

                    magnitude =
                        node->float_scale_val ==
                        INT64_MIN
                            ? (UINT64_C(1) << 63)
                            : (uint64_t)(
                                -node->float_scale_val
                            );

                } else {

                    magnitude =
                        (uint64_t)
                            node->float_scale_val;
                }

                integer_part =
                    magnitude /
                    (uint64_t)
                        U_SCALE_FACTOR;

                fraction_part =
                    magnitude %
                    (uint64_t)
                        U_SCALE_FACTOR;

                return append_fmt(
                    buf,
                    cap,
                    len,
                    "F:8:%s%llu.%08llu;",
                    negative
                        ? "-"
                        : "",
                    (unsigned long long)
                        integer_part,
                    (unsigned long long)
                        fraction_part
                );
            }

        case U_STRING:
            {
                size_t input_len;
                char* packed;
                size_t packed_len;
                int ok;

                if (!node->str_val) {
                    return append_cstr(
                        buf,
                        cap,
                        len,
                        "P:0:;"
                    );
                }

                input_len =
                    strlen(node->str_val);

                packed =
                    u_pack(
                        node->str_val,
                        input_len
                    );

                if (!packed) {
                    return 0;
                }

                packed_len =
                    strlen(packed);

                ok =
                    append_fmt(
                        buf,
                        cap,
                        len,
                        "P:%zu:%s;",
                        packed_len,
                        packed
                    );

                free(packed);

                return ok;
            }

        case U_ARRAY:
            {
                size_t i;

                if (node->arr_len != 0 &&
                    !node->arr_vals) {
                    return 0;
                }

                if (!append_fmt(
                    buf,
                    cap,
                    len,
                    "A:%zu[",
                    node->arr_len
                )) {
                    return 0;
                }

                for (
                    i = 0;
                    i < node->arr_len;
                    ++i
                ) {

                    if (!node->arr_vals[i]) {
                        return 0;
                    }

                    if (!u_serialize(
                        node->arr_vals[i],
                        buf,
                        cap,
                        len,
                        history,
                        hist_cap,
                        depth + 1
                    )) {
                        return 0;
                    }

                    if (i + 1 <
                        node->arr_len) {

                        if (!append_cstr(
                            buf,
                            cap,
                            len,
                            "|"
                        )) {
                            return 0;
                        }
                    }
                }

                return append_cstr(
                    buf,
                    cap,
                    len,
                    "]"
                );
            }

        case U_OBJECT:
            {
                size_t count =
                    node->obj_len;

                size_t* order = NULL;

                size_t i;

                if (count != 0 &&
                    (!node->obj_keys ||
                     !node->obj_vals)) {
                    return 0;
                }

                if (!append_fmt(
                    buf,
                    cap,
                    len,
                    "O:%zu{",
                    count
                )) {
                    return 0;
                }

                if (count > 0) {

                    if (count >
                        SIZE_MAX /
                        sizeof(size_t)) {
                        return 0;
                    }

                    order =
                        (size_t*)malloc(
                            count *
                            sizeof(size_t)
                        );

                    if (!order) {
                        return 0;
                    }

                    for (
                        i = 0;
                        i < count;
                        ++i
                    ) {
                        order[i] = i;
                    }

                    /*
                     * Stable insertion sort.
                     *
                     * The original object remains
                     * untouched.
                     */
                    for (
                        i = 1;
                        i < count;
                        ++i
                    ) {
                        size_t current =
                            order[i];

                        size_t j = i;

                        while (
                            j > 0 &&
                            strcmp(
                                node->obj_keys[
                                    order[j - 1]
                                ],
                                node->obj_keys[
                                    current
                                ]
                            ) > 0
                        ) {
                            order[j] =
                                order[j - 1];

                            --j;
                        }

                        order[j] =
                            current;
                    }
                }

                for (
                    i = 0;
                    i < count;
                    ++i
                ) {
                    size_t index =
                        order[i];

                    const char* key =
                        node->obj_keys[index];

                    char* packed_key;

                    size_t packed_key_len;

                    if (!key) {
                        free(order);
                        return 0;
                    }

                    packed_key =
                        u_pack(
                            key,
                            strlen(key)
                        );

                    if (!packed_key) {
                        free(order);
                        return 0;
                    }

                    packed_key_len =
                        strlen(packed_key);

                    if (!append_fmt(
                        buf,
                        cap,
                        len,
                        "K:%zu:%s->",
                        packed_key_len,
                        packed_key
                    )) {
                        free(packed_key);
                        free(order);
                        return 0;
                    }

                    free(packed_key);

                    if (!node->obj_vals[index]) {
                        free(order);
                        return 0;
                    }

                    if (!u_serialize(
                        node->obj_vals[index],
                        buf,
                        cap,
                        len,
                        history,
                        hist_cap,
                        depth + 1
                    )) {
                        free(order);
                        return 0;
                    }

                    if (i + 1 <
                        count) {

                        if (!append_cstr(
                            buf,
                            cap,
                            len,
                            "|"
                        )) {
                            free(order);
                            return 0;
                        }
                    }
                }

                free(order);

                return append_cstr(
                    buf,
                    cap,
                    len,
                    "}"
                );
            }

        default:
            return append_cstr(
                buf,
                cap,
                len,
                "NIL;"
            );
    }
}

/* ============================================================
 * PROCESS
 * ============================================================ */

UBRIDGE_API char* UBRIDGE_CALL
ub_process(UNode* root)
{
    char* buf;
    uintptr_t* history;
    size_t cap;
    size_t len;
    size_t hist_cap;
    uint32_t checksum;

    if (!root) {
        return NULL;
    }

    cap = 2048;
    len = 0;

    buf =
        (char*)malloc(cap);

    if (!buf) {
        return NULL;
    }

    buf[0] = '\0';

    hist_cap = 256;

    if (hist_cap >
        SIZE_MAX / sizeof(uintptr_t)) {
        free(buf);
        return NULL;
    }

    history =
        (uintptr_t*)malloc(
            hist_cap *
            sizeof(uintptr_t)
        );

    if (!history) {
        free(buf);
        return NULL;
    }

    if (!append_cstr(
        &buf,
        &cap,
        &len,
        "UB1;"
    )) {
        free(history);
        free(buf);
        return NULL;
    }

    if (!u_serialize(
        root,
        &buf,
        &cap,
        &len,
        &history,
        &hist_cap,
        0
    )) {
        free(history);
        free(buf);
        return NULL;
    }

    free(history);

    /*
     * FNV-1a provides deterministic integrity checking.
     * It is NOT cryptographic authentication.
     */
    checksum =
        compute_fnv1a(
            buf,
            len
        );

    if (!append_fmt(
        &buf,
        &cap,
        &len,
        "#CHK:%08X",
        checksum
    )) {
        free(buf);
        return NULL;
    }

    return buf;
}

/* ============================================================
 * FREE GRAPH
 * ============================================================ */

static int pointer_seen(
    UNode** nodes,
    size_t count,
    UNode* node
)
{
    size_t i;

    for (i = 0; i < count; ++i) {
        if (nodes[i] == node) {
            return 1;
        }
    }

    return 0;
}

static int collect_node(
    UNode* node,
    UNode*** nodes,
    size_t* count,
    size_t* capacity
)
{
    size_t i;

    if (!node) {
        return 1;
    }

    if (pointer_seen(
        *nodes,
        *count,
        node
    )) {
        return 1;
    }

    if (*count == SIZE_MAX) {
        return 0;
    }

    if (*count >= *capacity) {

        size_t new_cap;

        UNode** expanded;

        if (*capacity == 0) {
            new_cap = 256;
        } else {
            if (*capacity >
                SIZE_MAX / 2) {
                return 0;
            }

            new_cap =
                *capacity * 2;
        }

        if (new_cap <= *capacity ||
            new_cap >
                SIZE_MAX / sizeof(UNode*)) {
            return 0;
        }

        expanded =
            (UNode**)realloc(
                *nodes,
                new_cap *
                sizeof(UNode*)
            );

        if (!expanded) {
            return 0;
        }

        *nodes =
            expanded;

        *capacity =
            new_cap;
    }

    (*nodes)[*count] =
        node;

    (*count)++;

    if (node->arr_len != 0 &&
        !node->arr_vals) {
        return 0;
    }

    if (node->obj_len != 0 &&
        (!node->obj_keys ||
         !node->obj_vals)) {
        return 0;
    }

    for (
        i = 0;
        i < node->arr_len;
        ++i
    ) {
        if (!collect_node(
            node->arr_vals[i],
            nodes,
            count,
            capacity
        )) {
            return 0;
        }
    }

    for (
        i = 0;
        i < node->obj_len;
        ++i
    ) {
        if (!collect_node(
            node->obj_vals[i],
            nodes,
            count,
            capacity
        )) {
            return 0;
        }
    }

    return 1;
}

/* ============================================================
 * FREE
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_free(UNode* root)
{
    UNode** nodes = NULL;

    size_t count = 0;
    size_t capacity = 0;

    size_t i;

    if (!root) {
        return;
    }

    /*
     * Collect first.
     *
     * We never partially destroy the graph if collection
     * fails.
     */
    if (!collect_node(
        root,
        &nodes,
        &count,
        &capacity
    )) {
        free(nodes);
        return;
    }

    /*
     * Release owned payloads and containers.
     */
    for (
        i = 0;
        i < count;
        ++i
    ) {
        UNode* node =
            nodes[i];

        size_t j;

        free(node->str_val);

        if (node->obj_keys) {

            for (
                j = 0;
                j < node->obj_len;
                ++j
            ) {
                free(
                    node->obj_keys[j]
                );
            }
        }

        free(node->arr_vals);

        free(node->obj_keys);

        free(node->obj_vals);
    }

    /*
     * Release nodes only after all internal pointers have
     * been consumed.
     */
    for (
        i = 0;
        i < count;
        ++i
    ) {
        free(nodes[i]);
    }

    free(nodes);
}

/* ============================================================
 * STRING ALLOCATION RELEASE
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_string_free(char* ptr)
{
    free(ptr);
}

/* ============================================================
 * SCIENTIFIC PRECISION
 * ============================================================ */

UBRIDGE_API void UBRIDGE_CALL
ub_scientific(
    UNode* node,
    int64_t coefficient,
    int32_t exponent
)
{
    if (!node) {
        return;
    }

    node->type = U_FLOAT;

    node->precision_mode =
        UB_MODE_SCIENTIFIC;

    node->scientific_coeff =
        coefficient;

    node->scientific_exp =
        exponent;

    node->float_scale_val = 0;
}
