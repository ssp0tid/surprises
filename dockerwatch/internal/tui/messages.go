package tui

const (
	MsgRefresh = "refresh"
	MsgQuit = "quit"
	MsgError = "error"
)

type ContainerMsg struct {
	Type string
}

type StatsMsg struct {
	ContainerID string
}

type LogMsg struct {
	ContainerID string
}