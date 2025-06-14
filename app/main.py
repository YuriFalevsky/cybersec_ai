import typer, json
from fastapi import FastAPI, Form
import uvicorn

from .agent import URLAnalysisAgent

cli = typer.Typer(add_completion=False)
agent = URLAnalysisAgent()

@cli.command()
def run(
    prompt: str = typer.Option(..., help="Промт для LLM"),
    url: str   = typer.Option(..., help="Целевой URL")
):
    result = agent.analyze(prompt, url)
    print(json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else result)

app = FastAPI(title="AI-URL-Agent")

@app.post("/analyze") #api
async def analyze_api(prompt: str = Form(...), url: str = Form(...)):
    return {"result": agent.analyze(prompt, url)}

@cli.command()
def serve(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run("app.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    cli()
