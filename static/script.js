// Ensure the script runs after the DOM is fully loaded
window.onload = () => {
    // to know whether to recall recognition or not
    var speech_flag = false;         


    // Check for browser compatibility with SpeechRecognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    function fetch_response(query){
        // will fetch response from api url and return json
        const url = "/result";
        const data = {
            query_text : query
        };

        fetch(url, {
            method : "POST",
            headers : {
                "Content-Type" : "application/json"
            },
            body : JSON.stringify(data)
        })

        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }

            return response.json();
        })

        .then(data => {
            console.log(data);
            document.getElementById("response_p").innerText = data.response;
            speakText(data.response);
        })

        .catch(error => {
            console.log("problem with fetch :", error)
        });
    }

    function speakText(data) {
        // cancel any ongoing speech
        window.speechSynthesis.cancel();

        // break the text into chunks since it cant speak the whole text at once
        const chunks = data.split(/[.!?]+/)

        const speakChunk = (index) => {
            if (index < chunks.length) {
                const utterance = new SpeechSynthesisUtterance(chunks[index]);
                utterance.onend = () => speakChunk(index + 1);
                window.speechSynthesis.speak(utterance);
            }
        };
    
        // Start speaking the first chunk
        speakChunk(0);
    }

    
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        
        // Recognition settings
        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
    
        // Event handler for when the recognition service returns a result
        recognition.onresult = (event) => {
            const temp = event.results[0][0].transcript;
            console.log(temp);
            var result = fetch_response(temp);
        };

        // event handler to restart the recogn when it ends
        recognition.onend = () => {
            if(speech_flag){
                recognition.start();
            }
        };

        // Event handler for when the recognition service encounters an error
        recognition.onerror = (event) => {
            console.error('Error occurred in recognition: ', event.error);
        };
    
        // Set up click event handler on the body
        document.querySelector("#start").onclick = () => {
            console.log("recognition started");
            speech_flag = true;
            recognition.start();
        };

        // stop voice recognition
        document.querySelector("#stop").onclick = () => {
            console.log("recognition stopped");
            speech_flag = false;
            recognition.stop();
        }
    }

    else {
        console.log('Speech Recognition API not supported in this browser.');
    }
}; 