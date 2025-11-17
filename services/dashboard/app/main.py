import pandas as pd
import streamlit as st
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import LLMLog, LLMEvalResult


def load_basic_stats(db: Session):
    total_logs = db.scalar(select(func.count(LLMLog.id))) or 0
    total_eval = db.scalar(select(func.count(LLMEvalResult.id))) or 0

    label_counts = (
        db.execute(
            select(LLMEvalResult.label, func.count(LLMEvalResult.id)).group_by(
                LLMEvalResult.label
            )
        )
        .all()
        or []
    )

    return total_logs, total_eval, label_counts


def load_daily_scores(db: Session):
    stmt = (
        select(
            func.date(LLMEvalResult.created_at).label("day"),
            func.avg(LLMEvalResult.rule_score).label("avg_score"),
        )
        .group_by(func.date(LLMEvalResult.created_at))
        .order_by("day")
    )
    rows = db.execute(stmt).all() or []
    if not rows:
        return pd.DataFrame(columns=["day", "avg_score"])
    return pd.DataFrame(rows, columns=["day", "avg_score"])


def main():
    st.title("LLM Quality Observer - Dashboard")

    with SessionLocal() as db:
        total_logs, total_eval, label_counts = load_basic_stats(db)
        daily_scores_df = load_daily_scores(db)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Logs", total_logs)
    with col2:
        st.metric("Evaluated Logs", total_eval)

    st.subheader("Evaluation Label Distribution")
    if label_counts:
        labels, counts = zip(*label_counts)
        label_df = pd.DataFrame({"label": labels, "count": counts})
        st.bar_chart(label_df.set_index("label"))
    else:
        st.write("No evaluation data yet.")

    st.subheader("Average Rule Score by Day")
    if not daily_scores_df.empty:
        daily_scores_df = daily_scores_df.set_index("day")
        st.line_chart(daily_scores_df)
    else:
        st.write("No daily scores yet.")


if __name__ == "__main__":
    main()
