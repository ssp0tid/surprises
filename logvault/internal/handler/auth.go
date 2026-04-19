package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/golang-jwt/jwt/v5"
	"github.com/logvault/logvault/internal/config"
	"github.com/logvault/logvault/internal/model"
	"golang.org/x/crypto/bcrypt"
)

type AuthHandler struct {
	config *config.Config
}

func NewAuthHandler(cfg *config.Config) *AuthHandler {
	return &AuthHandler{config: cfg}
}

func (h *AuthHandler) Register(r chi.Router) {
	r.Post("/api/v1/auth/login", h.Login)
	r.Post("/api/v1/auth/logout", h.Logout)
	r.Get("/api/v1/auth/me", h.Me)
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	if !h.config.Auth.Enabled {
		WriteError(w, http.StatusForbidden, "FORBIDDEN", "authentication is disabled")
		return
	}

	var req model.AuthRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "invalid JSON body")
		return
	}

	if req.Username == "" || req.Password == "" {
		WriteError(w, http.StatusBadRequest, "MISSING_FIELD", "username and password required")
		return
	}

	if req.Username != h.config.Auth.Username {
		WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "invalid credentials")
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(h.config.Auth.Password), []byte(req.Password)); err != nil {
		WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "invalid credentials")
		return
	}

	token, err := h.generateToken(req.Username)
	if err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to generate token")
		return
	}

	resp := model.AuthResponse{
		Token: token,
		User: model.User{
			ID:       req.Username,
			Username: req.Username,
		},
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	resp := map[string]bool{"success": true}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *AuthHandler) Me(w http.ResponseWriter, r *http.Request) {
	user, ok := r.Context().Value("user").(string)
	if !ok {
		WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "not authenticated")
		return
	}

	resp := model.User{
		ID:       user,
		Username: user,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *AuthHandler) generateToken(username string) (string, error) {
	claims := jwt.MapClaims{
		"sub": username,
		"exp": time.Now().Add(h.config.Auth.TokenExpiry()).Unix(),
		"iat": time.Now().Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(h.config.Auth.JWTSecret))
}

func (h *AuthHandler) ValidateToken(tokenString string) (string, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		return []byte(h.config.Auth.JWTSecret), nil
	})
	if err != nil || !token.Valid {
		return "", err
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return "", jwt.ErrSignatureInvalid
	}

	sub, ok := claims["sub"].(string)
	if !ok {
		return "", jwt.ErrSignatureInvalid
	}

	return sub, nil
}

func ExtractToken(r *http.Request) string {
	auth := r.Header.Get("Authorization")
	if strings.HasPrefix(auth, "Bearer ") {
		return strings.TrimPrefix(auth, "Bearer ")
	}
	return ""
}

type Claims struct {
	jwt.RegisteredClaims
}

func InitAuth(username, password string) error {
	if password == "" {
		return nil
	}
	_, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return err
}