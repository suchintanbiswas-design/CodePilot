def build_index(users, documents):
    """Sequential loops that should not be classified as nested."""
    user_index = {}
    for user in users:
        user_index[user.id] = user

    doc_index = {}
    for doc in documents:
        doc_index[doc.id] = doc

    return user_index, doc_index
