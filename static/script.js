// Ensure the script runs after the DOM is fully loaded
window.onload = () => {
    // to know whether to recall recognition or not
    var speech_flag = false;         


    // Check for browser compatibility with SpeechRecognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
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