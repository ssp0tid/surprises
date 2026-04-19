package components

type Spinner struct{}

func NewSpinner() *Spinner {
	return &Spinner{}
}

func (s *Spinner) Render() string {
	return ""
}