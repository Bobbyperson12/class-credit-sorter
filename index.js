// Create an example func
const test = () => {
  console.log('Hello World!');
}

function handleFormSubmit(event) {
  // Prevent the form from submitting to a server
  event.preventDefault();

  // Get the value of the "major" input
  const majorValue = document.getElementById("major").value;
  const minorValue = document.getElementById("minors").value;
  const completedValue = document.getElementById("finishedClasses").value;
  let data_new = {
    degree: majorValue,
    minors: minorValue,
    completed: completedValue
  };
  fetch("http://localhost:8080/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data_new)  // Convert the data object to a JSON string
  })
    .then(response => response.json())  // Parse the response as JSON
    .then(data => {
      console.log(data);  // Log the parsed response data
    })
    .catch(error => {
      console.error("Error:", error);  // Log any errors
    });
}