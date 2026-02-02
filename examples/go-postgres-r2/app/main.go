package main

import (
	"database/sql"
	"log"
	"net/http"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
)

var db *sql.DB

type Todo struct {
	ID        int    `json:"id"`
	Title     string `json:"title"`
	Completed bool   `json:"completed"`
}

type CreateTodoRequest struct {
	Title     string `json:"title" binding:"required"`
	Completed bool   `json:"completed"`
}

func main() {
	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		log.Fatal("DATABASE_URL environment variable is required")
	}

	var err error
	db, err = sql.Open("postgres", databaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	if err = db.Ping(); err != nil {
		log.Fatalf("Failed to ping database: %v", err)
	}

	// Create table if not exists
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS todos (
			id SERIAL PRIMARY KEY,
			title VARCHAR(255) NOT NULL,
			completed BOOLEAN DEFAULT FALSE
		)
	`)
	if err != nil {
		log.Fatalf("Failed to create table: %v", err)
	}

	log.Println("Connected to PostgreSQL database")

	r := gin.Default()

	r.GET("/", rootHandler)
	r.GET("/todos", listTodos)
	r.POST("/todos", createTodo)
	r.GET("/todos/:id", getTodo)
	r.PUT("/todos/:id", updateTodo)
	r.DELETE("/todos/:id", deleteTodo)
	r.GET("/health", healthCheck)

	log.Println("Server starting on port 8080")
	r.Run(":8080")
}

func rootHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "Todo API - PostgreSQL backed up by NestVault",
	})
}

func listTodos(c *gin.Context) {
	rows, err := db.Query("SELECT id, title, completed FROM todos ORDER BY id")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var todos []Todo
	for rows.Next() {
		var todo Todo
		if err := rows.Scan(&todo.ID, &todo.Title, &todo.Completed); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		todos = append(todos, todo)
	}

	if todos == nil {
		todos = []Todo{}
	}

	c.JSON(http.StatusOK, todos)
}

func createTodo(c *gin.Context) {
	var req CreateTodoRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Title is required"})
		return
	}

	var todo Todo
	err := db.QueryRow(
		"INSERT INTO todos (title, completed) VALUES ($1, $2) RETURNING id, title, completed",
		req.Title, req.Completed,
	).Scan(&todo.ID, &todo.Title, &todo.Completed)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, todo)
}

func getTodo(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}

	var todo Todo
	err = db.QueryRow(
		"SELECT id, title, completed FROM todos WHERE id = $1", id,
	).Scan(&todo.ID, &todo.Title, &todo.Completed)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "Todo not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, todo)
}

func updateTodo(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}

	var req CreateTodoRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Title is required"})
		return
	}

	var todo Todo
	err = db.QueryRow(
		"UPDATE todos SET title = $1, completed = $2 WHERE id = $3 RETURNING id, title, completed",
		req.Title, req.Completed, id,
	).Scan(&todo.ID, &todo.Title, &todo.Completed)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "Todo not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, todo)
}

func deleteTodo(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}

	result, err := db.Exec("DELETE FROM todos WHERE id = $1", id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Todo not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Todo deleted"})
}

func healthCheck(c *gin.Context) {
	if err := db.Ping(); err != nil {
		c.JSON(http.StatusOK, gin.H{
			"status":   "unhealthy",
			"database": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":   "healthy",
		"database": "connected",
	})
}
