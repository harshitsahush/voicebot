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
            fetch_response(temp);
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

        // to start and stop speech recogn
        document.getElementById("start_stop").onclick = () => {
            if(speech_flag){
                speech_flag = false;
                recognition.stop()
                // chnage icon
                document.getElementById("start_stop").className = "button_red"
                console.log("Recognition stopped!")
            }

            else{
                speech_flag = true;
                recognition.start();
                // chnage icon
                document.getElementById("start_stop").className = "button_green"
                console.log("recognition started");
            }
        }
    
    }

    else {
        console.log('Speech Recognition API not supported in this browser.');
    }


    // fetches response from the flask api and write it in the paragraph
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

    // speaks the text
    function speakText(data) {
        // cancel any ongoing speech
        window.speechSynthesis.cancel();

        // break the text into chunks since it cant speak the whole text at once
        const chunks = data.split(/[.!?]+/)

        const speakChunk = (index) => {
            if (index < chunks.length) {
                const utterance = new SpeechSynthesisUtterance(chunks[index]);
                utterance.rate = 1.2;
                utterance.onend = () => speakChunk(index + 1);
                window.speechSynthesis.speak(utterance);
            }
        };
    
        // Start speaking the first chunk
        speakChunk(0);
    }

    // stop the response speech
    document.getElementById("stop_speech").onclick = () => {
        window.speechSynthesis.cancel();
        console.log("Speech stopped!")
    };

    // to process the uploaded file
    document.getElementById("upload_form").addEventListener("submit", function(event) {
        event.preventDefault();

        const file_input = document.getElementById("query_file");
        const file = file_input.files[0];

        if(file){
            // construct form data to send to url
            const form_data = new FormData();
            form_data.append("file", file);

            fetch("/process_file",{
                method : "POST",
                body : form_data
            })

            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
                window.alert("File uploaded successfully");
            })

            .catch(error => {
                console.error('Error:', error);
                window.alert("Please upload again.");
            });
        }
        
        else{
            window.alert("Please upload a valid file.");
        }
    });


};