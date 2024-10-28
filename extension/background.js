chrome.contextMenus.create({
  id: "deepfakeDetection",
  title: "Check if this image is a deepfake",
  contexts: ["image"]
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "deepfakeDetection") {
    const imageUrl = info.srcUrl;

    try {
      // Baixa a imagem para análise
      const response = await fetch(imageUrl);
      const blob = await response.blob();

      // Prepara os dados para enviar a imagem ao backend Flask
      const formData = new FormData();
      formData.append("file", blob, "image.jpg");

      // Envia a imagem para o servidor Flask para análise
      const serverResponse = await fetch("http://localhost:5000/upload_image", {
        method: "POST",
        body: formData
      });

      const result = await serverResponse.json();

      // Interpreta o resultado com base no campo "verdict"
      let message;
      if (result.success && result.verdict === "ai") {
        message = "This image is a deepfake!";
      } else if (result.success && result.verdict === "human") {
        message = "This image is not a deepfake.";
      } else {
        message = "Image could not be analyzed or is in an unsupported format.";
      }

      // Exibe o resultado no pop-up do Chrome
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (msg) => alert(msg),
        args: [message]
      });

    } catch (error) {
      console.error("Error:", error);
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (msg) => alert(msg),
        args: ["Failed to connect to the server."]
      });
    }
  }
});
