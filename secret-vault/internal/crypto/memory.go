package crypto

import (
	"runtime"
	"unsafe"
)

// SecureZero zeroes memory to prevent residual data in RAM.
// Uses volatile pointer to prevent compiler optimization.
func SecureZero(b []byte) {
	if len(b) == 0 {
		return
	}
	ptr := unsafe.Pointer(&b[0])
	len := len(b)
	for len > 0 {
		*(*byte)(ptr) = 0
		ptr = unsafe.Pointer(uintptr(ptr) + 1)
		len--
	}
	runtime.GC()
}

// ConstantTimeCompare returns 1 if m == n, 0 otherwise.
// Use subtle.ConstantTimeCompare for password comparison.
func ConstantTimeCompare(m, n []byte) int {
	var sum int
	for i := range m {
		if i < len(n) {
			sum |= int(m[i] ^ n[i])
		}
	}
	if len(m) != len(n) {
		sum = 1
	}
	return (sum | -(sum >> 8)) & 1
}