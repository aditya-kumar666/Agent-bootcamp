
using System;

namespace Models
{
    public class TodoItem
    {
        public int Id { get; set; }
        public string Title { get; set; }
        public bool IsDone { get; set; } = false;
        public DateTime CreatedAtUtc { get; set; }

        public TodoItem(int id