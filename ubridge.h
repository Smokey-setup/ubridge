#ifndef UBRIDGE_H
#define UBRIDGE_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ==================
 * ABI / API VERSION
 * ================== */

#define UBRIDGE_API_MAJOR 1
#define UBRIDGE_API_MINOR 0

/* ====================
 * NODE TYPE IDENTIFIERS
 * ==================== */

#define U_NULL    UINT8_C(0)
#define U_INT     UINT8_C(1)
#define U_FLOAT   UINT8_C(2)
#define U_STRING  UINT8_C(3)
#define U_BOOL    UINT8_C(4)
#define U_ARRAY   UINT8_C(5)
#define U_OBJECT  UINT8_C(6)

/* =========================
 * FLOATING-POINT PRECISION
 * ========================= */

/*
 * Fixed-point scale:
 *
 *     stored_value = real_value * U_SCALE_FACTOR
 *
 * 8 decimal places are represented in fixed mode.
 */
#define U_SCALE_FACTOR INT64_C(100000000)

/* =================
 * PRECISION MODES
 * ================= */

#define UB_MODE_FIXED       UINT8_C(1)
#define UB_MODE_SCIENTIFIC  UINT8_C(2)

/* =====================
 * SERIALIZATION LIMITS
 * ===================== */

/*
 * Hard recursion limit for AST serialization.
 * Prevents attacker-controlled/degenerated trees from
 * exhausting the native stack.
 */
#define UB_MAX_SERIALIZE_DEPTH 1024

/* ============
 * STATUS CODES
 * ============ */

#define UB_OK              0
#define UB_ERR_INVALID    -1
#define UB_ERR_NOMEM      -2
#define UB_ERR_OVERFLOW   -3
#define UB_ERR_DEPTH      -4
#define UB_ERR_CYCLE      -5
#define UB_ERR_SERIALIZE  -6

/* ========
 * AST NODE
 * ======== */

/*
 * UNode is the in-process AST representation.
 *
 * IMPORTANT:
 * UNode contains native pointers and therefore is NOT a
 * portable wire/shared-memory representation.
 *
 * It must never be memcpy'd into shared memory and interpreted
 * as a UNode by another process.
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

    /*
     * Internal node identity used only for cycle detection
     * during serialization.
     *
     * It is NOT a persistent identifier and MUST NOT be used
     * as a cross-process identifier.
     */
    uintptr_t mem_id;

    /*
     * Floating-point representation mode.
     */
    uint8_t precision_mode;

    /*
     * Scientific representation:
     *
     * value = scientific_coeff * 10^scientific_exp
     */
    int32_t scientific_exp;
    int64_t scientific_coeff;

    /*
     * Non-cryptographic integrity/checkpoint value.
     *
     * FNV-1a is NOT a cryptographic hash.
     */
    uint32_t math_hash_checkpoint;

} UNode;

/* ===============================
 * API EXPORT / CALLING CONVENTION
 * =============================== */

#ifdef _WIN32

    #ifdef UBRIDGE_BUILD
        #define UBRIDGE_API __declspec(dllexport)
    #else
        #define UBRIDGE_API __declspec(dllimport)
    #endif

    #ifndef UBRIDGE_CALL
        #define UBRIDGE_CALL __cdecl
    #endif

#else

    #define UBRIDGE_API \
        __attribute__((visibility("default")))

    #define UBRIDGE_CALL

#endif

/* ==============
 * NODE CREATION
 * ============== */

UBRIDGE_API UNode* UBRIDGE_CALL
ub_create(uint8_t type);

/* ===================
 * NODE VALUE SETTERS
 * =================== */

UBRIDGE_API void UBRIDGE_CALL
ub_int(
    UNode* node,
    int64_t val
);

UBRIDGE_API void UBRIDGE_CALL
ub_float(
    UNode* node,
    double val
);

UBRIDGE_API void UBRIDGE_CALL
ub_str(
    UNode* node,
    const char* val
);

UBRIDGE_API void UBRIDGE_CALL
ub_scientific(
    UNode* node,
    int64_t coefficient,
    int32_t exponent
);

/* ====================
 * CONTAINER BUILDERS
 * ==================== */

UBRIDGE_API void UBRIDGE_CALL
ub_array(
    UNode* arr_node,
    UNode* item_node
);

UBRIDGE_API void UBRIDGE_CALL
ub_object(
    UNode* obj_node,
    const char* key,
    UNode* val_node
);

/* =============
 * SERIALIZATION
 * ============= */

/*
 * Returns a newly allocated, NUL-terminated serialization.
 *
 * Ownership:
 *     Caller owns the returned buffer.
 *     Release it with ub_string_free().
 *
 * Returns:
 *     NULL on invalid input, allocation failure, overflow,
 *     serialization failure, or excessive depth.
 */
UBRIDGE_API char* UBRIDGE_CALL
ub_process(
    UNode* root
);

/* ==================
 * MEMORY MANAGEMENT
 * ================== */

/*
 * Frees the complete node graph rooted at root.
 *
 * Handles repeated references/cycles without double-freeing
 * nodes.
 */
UBRIDGE_API void UBRIDGE_CALL
ub_free(
    UNode* root
);

/*
 * Releases memory returned by ub_process().
 */
UBRIDGE_API void UBRIDGE_CALL
ub_string_free(
    char* ptr
);

/* ===============================
 * NOTE ABOUT THE OLD RING BUFFER
 * =============================== */

/*
 * The previous ub_ring_t / ub_ring_push() / ub_ring_pop()
 * interface has intentionally been removed.
 *
 * A UNode contains process-local pointers and therefore cannot
 * be safely copied into a cross-process shared-memory ring.
 *
 * A production IPC ring must use a defined wire representation
 * containing bytes/relative offsets plus an explicit
 * synchronization protocol.
 *
 * The shared-memory ABI must therefore NOT expose UNode directly.
 */

#ifdef __cplusplus
}
#endif

#endif /* UBRIDGE_H */
