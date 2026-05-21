package utils

type TrafixError interface {
	error
	StatusCode() int
	Code() string
}

type trafixError struct {
	code       string
	statusCode int
	message    string
}

func (e *trafixError) Error() string {
	return e.message
}

func (e *trafixError) StatusCode() int {
	return e.statusCode
}

func (e *trafixError) Code() string {
	return e.code
}

func NewTrafixError(code string, statusCode int, message string) TrafixError {
	return &trafixError{
		code:       code,
		statusCode: statusCode,
		message:    message,
	}
}

var (
	ErrNotFound       = NewTrafixError("not_found", 404, "resource not found")
	ErrUnauthorized  = NewTrafixError("unauthorized", 401, "unauthorized")
	ErrForbidden     = NewTrafixError("forbidden", 403, "forbidden")
	ErrRateLimited   = NewTrafixError("rate_limited", 429, "rate limited")
	ErrBadRequest    = NewTrafixError("bad_request", 400, "bad request")
	ErrInternalServer = NewTrafixError("internal_server_error", 500, "internal server error")
	ErrBadGateway   = NewTrafixError("bad_gateway", 502, "bad gateway")
	ErrTimeout      = NewTrafixError("timeout", 504, "timeout")
)

func ErrNotFoundWithMsg(msg string) TrafixError {
	return NewTrafixError("not_found", 404, msg)
}

func ErrUnauthorizedWithMsg(msg string) TrafixError {
	return NewTrafixError("unauthorized", 401, msg)
}

func ErrForbiddenWithMsg(msg string) TrafixError {
	return NewTrafixError("forbidden", 403, msg)
}

func ErrRateLimitedWithMsg(msg string) TrafixError {
	return NewTrafixError("rate_limited", 429, msg)
}

func ErrBadRequestWithMsg(msg string) TrafixError {
	return NewTrafixError("bad_request", 400, msg)
}

func ErrInternalServerWithMsg(msg string) TrafixError {
	return NewTrafixError("internal_server_error", 500, msg)
}

func ErrBadGatewayWithMsg(msg string) TrafixError {
	return NewTrafixError("bad_gateway", 502, msg)
}

func ErrTimeoutWithMsg(msg string) TrafixError {
	return NewTrafixError("timeout", 504, msg)
}