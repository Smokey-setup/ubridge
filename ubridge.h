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

/* Precision Mode Identifiers for Hybrid Engine */
#define UB_MODE_FIXED       1
#define UB_MODE_SCIENTIFIC  2

/* 
 * Abstract Syntax Tree Node for FFI boundary transfer.
 * Note: Upgraded with flat hybrid precision fields and cryptographic state checkpoints 
 * while maintaining strict C89/C99 ABI compatibility.
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

    uint8_t precision_mode;       // Tracks UB_MODE_FIXED vs UB_MODE_SCIENTIFIC
    int32_t scientific_exp;       // Exponent for extreme scale physics/astronomy
    int64_t scientific_coeff;     // Coefficient significant digits
    uint32_t math_hash_checkpoint;// Rolling FNV-1a checksum state fingerprint
} UNode;

/* 
 * Atomic Single-Producer/Single-Consumer (SPSC) Shared Memory Ring Buffer
 * Enables zero-copy, zero-serialization cross-process IPC between Node.js, Python, and C.
 */
typedef struct ub_ring_t {
    size_t capacity;
    volatile size_t head;
    volatile size_t tail;
    volatile uint64_t version_seq;
    UNode nodes[1]; // Flexible array member mapped directly into shared RAM
} ub_ring_t;

/* Cross-Platform Export Directives */
#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif


EXPORT UNode* ub_create(uint8_t type);
EXPORT void ub_int(UNode* node, int64_t val);
EXPORT void ub_float(UNode* node, double val);
EXPORT void ub_str(UNode* node, const char* val);
EXPORT void ub_array(UNode* arr_node, UNode* item_node);
EXPORT void ub_object(UNode* obj_node, const char* key, UNode* val_node);
EXPORT const char* ub_process(UNode* root);
EXPORT void ub_free(UNode* root);
EXPORT void ub_string_free(char* ptr);
EXPORT void ub_scientific(UNode* node, int64_t coefficient, int32_t exponent);
EXPORT ub_ring_t* ub_ring_init(void* buffer_ptr, size_t capacity_nodes);
EXPORT int ub_ring_push(ub_ring_t* ring, const UNode* node);
EXPORT int ub_ring_pop(ub_ring_t* ring, UNode* out_node);

#ifdef __cplusplus
}
#endif

#endif // UBRIDGE_H
