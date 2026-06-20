# Streamlit Community Cloud Deployment

To deploy this project to Streamlit Community Cloud:

1. Push your repository to GitHub.
2. Create a new app on Streamlit Cloud and point it to the repository and branch.
3. Set the main file to `src/support_agent/presentation/streamlit_app.py` and the command to:

```
streamlit run src/support_agent/presentation/streamlit_app.py
```

4. Add secrets (OpenAI API key) in the Streamlit Cloud UI (do not commit them in `.env`).
5. Use `requirements.txt` as the dependency file. If deploying on Streamlit Cloud, ensure large packages like `sentence-transformers` are supported by the build environment.
