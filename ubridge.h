#ifndef UBRIDGE_H
#define UBRIDGE_H

#include <stdint.h>
#include <stddef.h>

/* Cross-Language Linkage Guard */
#ifdef __cplusplus
extern "C" {
#endif

/* Data Type Identifiers */
#define U_NULL    0
#define U_INT     1
#define U_FLOAT   2
#define U_STRING  3
#define U_BOOL    4
#define U_ARRAY   5
#define U_OBJECT  6

/* Precision scale for IEEE 754 float drift correction */
#define U_SCALE_FACTOR 100000000LL

/* 
 * Abstract Syntax Tree Node for FFI boundary transfer.
 * Note: Maintained as a flat struct for maximum C89/C99 ABI compatibility.
 */
typedef struct UNode {
    uint8_t type;
    int64_t int_val;
    int64_t float_scale_val;
    char* str_val;
    
    struct UNode** arr_vals;
    size_t arr_len;
    
    char** obj_keys;
    struct UNode** obj_vals;
    size_t obj_len;
    
    uintptr_t mem_id;
} UNode;

/* Cross-Platform Export Directives */
#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif

/* Public API Surface */
EXPORT UNode* ub_create(uint8_t type);
EXPORT void ub_int(UNode* node, int64_t val);
EXPORT void ub_float(UNode* node, double val);
EXPORT void ub_str(UNode* node, const char* val);
EXPORT void ub_array(UNode* arr_node, UNode* item_node);
EXPORT void ub_object(UNode* obj_node, const char* key, UNode* val_node);
EXPORT const char* ub_process(UNode* root);
EXPORT void ub_free(UNode* root);
EXPORT void ub_string_free(char* ptr);

#ifdef __cplusplus
}
#endif

#endif // UBRIDGE_H
