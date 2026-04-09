__all__ = ["Agent", "SearchDocsTool", "ListDocsTool", "GetDocInfoTool", "CreateDocTool", "DeleteDocTool"]


def __getattr__(name: str):
    if name == "Agent":
        from services.agent.agent import Agent
        return Agent
    if name == "SearchDocsTool":
        from services.agent.tools.search_docs import SearchDocsTool
        return SearchDocsTool
    if name == "ListDocsTool":
        from services.agent.tools.list_docs import ListDocsTool
        return ListDocsTool
    if name == "GetDocInfoTool":
        from services.agent.tools.get_doc_info import GetDocInfoTool
        return GetDocInfoTool
    if name == "CreateDocTool":
        from services.agent.tools.create_doc import CreateDocTool
        return CreateDocTool
    if name == "DeleteDocTool":
        from services.agent.tools.delete_doc import DeleteDocTool
        return DeleteDocTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
