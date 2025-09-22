import gradio as gr

def placeholder_fn(name):
    return f"Hello, {name}! The CV Screener is booting up."

iface = gr.Interface(
    fn=placeholder_fn,
    inputs="text",
    outputs="text",
    title="AI-Powered CV Screener",
    description="Docker environment is running successfully. Full application coming soon."
)

if __name__ == "__main__":
    iface.launch()