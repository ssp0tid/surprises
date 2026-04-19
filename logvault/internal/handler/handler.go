package handler

import (
	"encoding/json"
	"net/http"

	"github.com/logvault/logvault/internal/model"
)

type ValidationError struct {
	Field  string
	Reason string
}

func (e *ValidationError) Error() string {
	return e.Field + ": " + e.Reason
}

func WriteError(w http.ResponseWriter, status int, code string, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	resp := model.ErrorResponse{
		Error: model.ErrorDetail{
			Code:    code,
			Message: message,
		},
	}
	json.NewEncoder(w).Encode(resp)
}

func WriteJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if data != nil {
		json.NewEncoder(w).Encode(data)
	}
}