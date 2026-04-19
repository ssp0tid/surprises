package app

import (
	"encoding/json"
	"time"

	"github.com/boltdb/bolt"
)

type Store struct {
	db         *bolt.DB
	History     []RequestHistory
	Collections []Collection
}

func NewStore() (*Store, error) {
	db, err := bolt.Open("apitest.db", 0600, nil)
	if err != nil {
		return nil, err
	}

	err = db.Update(func(tx *bolt.Tx) error {
		buckets := []string{"history", "collections"}
		for _, b := range buckets {
			_, err := tx.CreateBucketIfNotExists([]byte(b))
			if err != nil {
				return err
			}
		}
		return nil
	})

	if err != nil {
		return nil, err
	}

	return &Store{db: db}, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) SaveRequestHistory(history RequestHistory) error {
	return s.db.Update(func(tx *bolt.Tx) error {
		data, err := json.Marshal(history)
		if err != nil {
			return err
		}
		return tx.Bucket([]byte("history")).Put([]byte(history.ID), data)
	})
}

func (s *Store) GetHistory() ([]RequestHistory, error) {
	var history []RequestHistory
	err := s.db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("history"))
		c := b.Cursor()
		for k, v := c.Last(); k != nil; k, v = c.Prev() {
			var h RequestHistory
			if err := json.Unmarshal(v, &h); err == nil {
				history = append(history, h)
			}
		}
		return nil
	})
	return history, err
}

func (s *Store) SaveCollection(collection Collection) error {
	return s.db.Update(func(tx *bolt.Tx) error {
		data, err := json.Marshal(collection)
		if err != nil {
			return err
		}
		return tx.Bucket([]byte("collections")).Put([]byte(collection.ID), data)
	})
}

func (s *Store) GetCollections() ([]Collection, error) {
	var collections []Collection
	err := s.db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("collections"))
		c := b.Cursor()
		for k, v := c.First(); k != nil; k, v = c.Next() {
			var col Collection
			if err := json.Unmarshal(v, &col); err == nil {
				collections = append(collections, col)
			}
		}
		return nil
	})
	return collections, err
}

func (s *Store) DeleteCollection(id string) error {
	return s.db.Update(func(tx *bolt.Tx) error {
		return tx.Bucket([]byte("collections")).Delete([]byte(id))
	})
}

func (s *Store) DeleteHistoryItem(id string) error {
	return s.db.Update(func(tx *bolt.Tx) error {
		return tx.Bucket([]byte("history")).Delete([]byte(id))
	})
}

type historyItem struct {
	ID        string
	Method    string
	URL       string
	Status    int
	Duration  int64
	Timestamp time.Time
}

func newHistoryItem(h RequestHistory) historyItem {
	return historyItem{
		ID:        h.ID,
		Method:    h.Request.Method,
		URL:       h.Request.URL,
		Status:    h.StatusCode,
		Duration: h.Duration,
		Timestamp: h.Timestamp,
	}
}

func (s *Store) Load() error {
	history, err := s.GetHistory()
	if err != nil {
		return err
	}
	s.History = history

	collections, err := s.GetCollections()
	if err != nil {
		return err
	}
	s.Collections = collections

	return nil
}
}