import { useState } from "react";
import "./App.css";
import ITI from "./assets/ITI.png";

const API_URL = "http://localhost:8000/chat_and_query";

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome back Mr. Azran. How may I be of assistance to you in your database today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);
  
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });
      const data = await response.json();
  
      // Format the query result into a readable string
      const formattedResult = JSON.stringify(data.response, null, 2);
  
      // Add the formatted result as the assistant's response
      setMessages([
        ...newMessages,
        { role: "assistant", content: formattedResult },
      ]);
    } catch (error) {
      console.error("Error fetching response:", error.message);
    }
    setLoading(false);
  };

  return (
    <>
      <div className="title-card">
        <img className="iti-pic" src={ITI} alt="" />
        <h1 className="title-h1">ITI GraphRAG Bot 3000</h1>
        <h1 className="hide">k</h1>
      </div>
      <div className="container">
        <div className="scroll-area">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
        </div>
        <div className="input-group">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your prompt here..."
          />
          <button onClick={sendMessage} disabled={loading}>
            {loading ? "Prompting..." : "Prompt"}
          </button>
        </div>
      </div>
    </>
  );
}

export default App;
