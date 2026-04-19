package components

type Progress struct{}

func NewProgress() *Progress {
	return &Progress{}
}

func (p *Progress) Render() string {
	return ""
}