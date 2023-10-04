// Create an example func
const test = () => {
  console.log('Hello World!');
}

// Define the data
const data = {
  degree: "CS-Major",
  other_info: 123
};

// Make the POST 
const posttest = () => {
  fetch("http://localhost:8080/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)  // Convert the data object to a JSON string
  })
    .then(response => response.json())  // Parse the response as JSON
    .then(data => {
      console.log(data);  // Log the parsed response data
    })
    .catch(error => {
      console.error("Error:", error);  // Log any errors
    });
}