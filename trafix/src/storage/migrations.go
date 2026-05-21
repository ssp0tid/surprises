package storage

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/rs/zerolog"
	"github.com/jmoiron/sqlx"
)

type Migrations struct {
	db     *sqlx.DB
	logger zerolog.Logger
}

func NewMigrations(db *sqlx.DB) *Migrations {
	return &Migrations{
		db:     db,
		logger: zerolog.New(os.Stdout).With().Timestamp().Logger(),
	}
}

func (m *Migrations) Run() error {
	if err := m.ensureMigrationTable(); err != nil {
		return fmt.Errorf("failed to ensure migration table: %w", err)
	}

	applied, err := m.getAppliedMigrations()
	if err != nil {
		return fmt.Errorf("failed to get applied migrations: %w", err)
	}

	migrationFiles, err := m.getMigrationFiles()
	if err != nil {
		return fmt.Errorf("failed to get migration files: %w", err)
	}

	for _, mf := range migrationFiles {
		if applied[mf.version] {
			m.logger.Debug().Str("version", mf.version).Msg("migration already applied")
			continue
		}

		m.logger.Info().Str("version", mf.version).Msg("applying migration")
		if err := m.applyMigration(mf); err != nil {
			return fmt.Errorf("failed to apply migration %s: %w", mf.version, err)
		}
	}

	return nil
}

func (m *Migrations) ensureMigrationTable() error {
	query := `
	CREATE TABLE IF NOT EXISTS schema_migrations (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		version TEXT NOT NULL UNIQUE,
		applied_at TEXT NOT NULL DEFAULT (datetime('now'))
	)`
	_, err := m.db.Exec(query)
	return err
}

func (m *Migrations) getAppliedMigrations() (map[string]bool, error) {
	rows, err := m.db.Query("SELECT version FROM schema_migrations")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	applied := make(map[string]bool)
	for rows.Next() {
		var version string
		if err := rows.Scan(&version); err != nil {
			return nil, err
		}
		applied[version] = true
	}

	return applied, nil
}

type migrationFile struct {
	version string
	path    string
	name   string
}

func (m *Migrations) getMigrationFiles() ([]migrationFile, error) {
	dirs := []string{
		".",
		"..",
		"../..",
		"/etc/trafix",
	}

	var migrationDir string
	for _, dir := range dirs {
		testPath := filepath.Join(dir, "migrations")
		if _, err := os.Stat(testPath); err == nil {
			migrationDir = testPath
			break
		}
	}

	if migrationDir == "" {
		migrationDir = "migrations"
	}

	entries, err := os.ReadDir(migrationDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read migrations directory: %w", err)
	}

	var files []migrationFile
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if !strings.HasSuffix(entry.Name(), ".sql") {
			continue
		}

		version := strings.TrimSuffix(entry.Name(), ".sql")
		files = append(files, migrationFile{
			version: version,
			name:   entry.Name(),
			path:   filepath.Join(migrationDir, entry.Name()),
		})
	}

	sort.Slice(files, func(i, j int) bool {
		return files[i].version < files[j].version
	})

	return files, nil
}

func (m *Migrations) applyMigration(mf migrationFile) error {
	content, err := os.ReadFile(mf.path)
	if err != nil {
		return fmt.Errorf("failed to read migration file: %w", err)
	}

	tx, err := m.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	if _, err := tx.Exec(string(content)); err != nil {
		return fmt.Errorf("failed to execute migration: %w", err)
	}

	if _, err := tx.Exec(
		"INSERT INTO schema_migrations (version) VALUES (?)",
		mf.version,
	); err != nil {
		return fmt.Errorf("failed to record migration: %w", err)
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit migration: %w", err)
	}

	m.logger.Info().Str("version", mf.version).Msg("migration applied successfully")
	return nil
}

func (m *Migrations) GetDB() *sqlx.DB {
	return m.db
}