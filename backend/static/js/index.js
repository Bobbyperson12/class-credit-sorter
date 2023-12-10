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
    .then(response => response.blob())  // Parse the response as JSON
    .then(blob => {
      console.log(blob);  // Log the parsed response data
          // Create a new object URL for the blob
      const url = window.URL.createObjectURL(blob);

      // Create a link element
      const a = document.createElement('a');

      // Set the download attribute and href
      a.href = url;
      a.download = 'downloaded.pdf'; // You can name the file here

      // Append the link to the body
      document.body.appendChild(a);

      // Trigger the download
      a.click();

      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    })
    .catch(error => {
      console.error("Error:", error);  // Log any errors
    });
}

function logout() {
  window.location.href = "/logout"
}