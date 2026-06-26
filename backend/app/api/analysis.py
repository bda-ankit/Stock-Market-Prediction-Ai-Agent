from fastapi import (
    APIRouter,
    UploadFile,
    File, Form
)
from tools.technical_tool import (
    technical_analysis_tool
)

from agents.stock_agent import (
    stock_agent
)

from services.file_parser import (
    prepare_market_dataframe
)

router = APIRouter(
    prefix="/api",
    tags=["Analysis"]
)

@router.post("/agent-test")
async def agent_test(
    file: UploadFile = File(...),
    news_text: str = Form("")
):

    content = await file.read()

    df = prepare_market_dataframe(
        content,
        file.filename
    )

    result = await stock_agent.analyze(
        dataframe=df,
        news_text=news_text
    )

    return result

@router.post("/technical-test")
async def technical_test(
    file: UploadFile = File(...)
):

    content = await file.read()

    df = prepare_market_dataframe(
        content,
        file.filename
    )

    analysis = (
        technical_analysis_tool(df)
    )

    return analysis


@router.post("/upload-test")
async def upload_test(
    file: UploadFile = File(...)
):

    content = await file.read()

    df = prepare_market_dataframe(
        content,
        file.filename
    )

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "start_date": str(
            df["date"].iloc[0]
        ),
        "end_date": str(
            df["date"].iloc[-1]
        )
    }