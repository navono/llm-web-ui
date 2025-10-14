"""Example data for the Gradio interface."""

# Example data for different media types
image_examples = [
    ["Perform OCR on the image...", "examples/images/1.jpg"],
    ["Caption the image. Describe the safety measures shown in the image. Conclude whether the situation is (safe or unsafe)...", "examples/images/2.jpg"],
    ["Solve the problem...", "examples/images/3.png"],
]

video_examples = [["Explain the Ad video in detail.", "examples/videos/1.mp4"], ["Explain the video in detail.", "examples/videos/2.mp4"]]

pdf_examples = [["Extract the content precisely.", "examples/pdfs/doc1.pdf"], ["Analyze and provide a short report.", "examples/pdfs/doc2.pdf"]]

gif_examples = [["Describe this GIF.", "examples/gifs/1.gif"], ["Describe this GIF.", "examples/gifs/2.gif"]]

caption_examples = [["examples/captions/1.JPG"], ["examples/captions/2.jpeg"], ["examples/captions/3.jpeg"]]
