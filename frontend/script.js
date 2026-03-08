console.log("Script carregado com sucesso!");

const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    
    if (sender === 'bot') {
        // O Marked.js transforma o Markdown em HTML estruturado
        div.innerHTML = marked.parse(text);
    } else {
        div.innerText = text;
    }
    
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function handleSend() {
    console.log("Botão clicado!"); // Aparece no F12
    const text = userInput.value.trim();
    
    if (!text) return;

    // 1. Mostrar na tela antes de chamar a API
    addMessage(text, 'user');
    userInput.value = '';

    try {
        const response = await fetch('http://localhost:8000/v1/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: text, 
                session_id: "alef-session-001" 
            })
        });

        const data = await response.json();
        addMessage(data.answer, 'bot');
    } catch (error) {
        console.error("Erro na API:", error);
        addMessage("Erro ao falar com o motor de IA.", 'bot');
    }
}

// Vincula os eventos
sendBtn.onclick = handleSend;

userInput.onkeypress = (e) => {
    if (e.key === 'Enter') handleSend();
};