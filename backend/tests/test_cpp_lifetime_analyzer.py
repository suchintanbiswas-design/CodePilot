import pytest
from app.engine.cpp_analyzer import CppLifetimeAnalyzer
from app.engine.static_analyzer import StaticAnalyzer
from app.engine.hybrid_engine import HybridEngine


# ---------------------------------------------------------------------------
# Unit-level CppLifetimeAnalyzer tests
# ---------------------------------------------------------------------------

def test_raw_pointer_returned_from_vector_indexed():
    """return &inventory[id] — indexed access."""
    analyzer = CppLifetimeAnalyzer()
    code = """
    #include <vector>
    class Book {};
    std::vector<Book> inventory;

    Book* findBookById(int id) {
        return &inventory[id];
    }
    """
    issues = analyzer.analyze(code)
    assert len(issues) == 1
    assert "Returning a raw pointer" in issues[0]["description"]
    assert issues[0]["severity"] == "Critical"


def test_raw_pointer_returned_from_vector_rangefor():
    """return &book where book is a range-for reference."""
    analyzer = CppLifetimeAnalyzer()
    code = """
    class Book {};
    class LibraryManager {
        std::vector<Book> inventory;
        Book* findBookById(int id) {
            for (auto& book : inventory) {
                if (book.id == id) {
                    return &book;
                }
            }
            return nullptr;
        }
    };
    """
    issues = analyzer.analyze(code)
    ret_issues = [i for i in issues if "Returning a raw pointer" in i["description"]]
    assert len(ret_issues) == 1
    assert "inventory" in ret_issues[0]["description"]
    assert ret_issues[0]["severity"] == "Critical"


def test_library_manager_erasure_rangefor():
    """removeBorrowedBooks().erase invalidates User::currentBook
    when findBookById uses range-for + return &book."""
    analyzer = CppLifetimeAnalyzer()
    code = """
    class LibraryManager {
        std::vector<Book> inventory;
        void removeBorrowedBooks() {
            inventory.erase(inventory.begin());
        }
        Book* findBookById(int id) {
            for (auto& book : inventory) {
                if (book.id == id) { return &book; }
            }
            return nullptr;
        }
    };
    class User {
        Book* currentBook;
        void borrow(LibraryManager& lib) {
            Book* book = lib.findBookById(42);
            currentBook = book;
        }
    };
    """
    issues = analyzer.analyze(code)
    erasure = [i for i in issues if "Container erasure" in i["description"]]
    assert len(erasure) >= 1
    assert any("currentBook" in e["description"] for e in erasure)


def test_library_manager_reallocation_rangefor():
    """addBook().push_back invalidates User::currentBook
    when findBookById uses range-for + return &book."""
    analyzer = CppLifetimeAnalyzer()
    code = """
    class LibraryManager {
        std::vector<Book> inventory;
        void addBook() {
            inventory.push_back(Book());
        }
        Book* findBookById(int id) {
            for (auto& book : inventory) {
                if (book.id == id) { return &book; }
            }
            return nullptr;
        }
    };
    class User {
        Book* currentBook;
        void borrow(LibraryManager& lib) {
            Book* book = lib.findBookById(42);
            currentBook = book;
        }
    };
    """
    issues = analyzer.analyze(code)
    realloc = [i for i in issues if "Vector reallocation" in i["description"]]
    assert len(realloc) >= 1
    assert any("currentBook" in r["description"] for r in realloc)


def test_library_manager_erasure_indexed():
    """Erasure with indexed return &inventory[id]."""
    analyzer = CppLifetimeAnalyzer()
    code = """
    class LibraryManager {
        std::vector<Book> inventory;
        void removeBorrowedBooks() {
            inventory.erase(inventory.begin());
        }
        Book* findBookById(int id) {
            return &inventory[id];
        }
    };
    class User {
        Book* currentBook;
        void borrow(LibraryManager& lib) {
            currentBook = lib.findBookById(42);
        }
    };
    """
    issues = analyzer.analyze(code)
    erasure = [i for i in issues if "Container erasure" in i["description"]]
    assert len(erasure) == 1
    assert "currentBook" in erasure[0]["description"]


def test_library_manager_reallocation_indexed():
    """Reallocation with indexed return &inventory[id]."""
    analyzer = CppLifetimeAnalyzer()
    code = """
    class LibraryManager {
        std::vector<Book> inventory;
        void addBook() {
            inventory.push_back(Book());
        }
        Book* findBookById(int id) {
            return &inventory[id];
        }
    };
    class User {
        Book* currentBook;
        void borrow(LibraryManager& lib) {
            currentBook = lib.findBookById(42);
        }
    };
    """
    issues = analyzer.analyze(code)
    realloc = [i for i in issues if "Vector reallocation" in i["description"]]
    assert len(realloc) == 1
    assert "currentBook" in realloc[0]["description"]


def test_double_free():
    analyzer = CppLifetimeAnalyzer()
    code = """
    void memoryLeak() {
        Book* b = new Book();
        Book* c = b;
        delete b;
        delete c; // double free
    }
    """
    issues = analyzer.analyze(code)
    assert len(issues) == 1
    assert "Double free" in issues[0]["description"]


def test_safe_shared_ptr():
    analyzer = CppLifetimeAnalyzer()
    code = """
    #include <vector>
    #include <memory>
    class Book {};
    std::vector<std::shared_ptr<Book>> inventory;

    std::shared_ptr<Book> getBook(int id) {
        return inventory[id];
    }

    void addAndRemove() {
        std::shared_ptr<Book> b = inventory[0];
        inventory.push_back(std::make_shared<Book>());
        inventory.erase(inventory.begin());
    }
    """
    issues = analyzer.analyze(code)
    assert len(issues) == 0


def test_safe_weak_ptr():
    analyzer = CppLifetimeAnalyzer()
    code = """
    #include <memory>
    #include <vector>
    std::vector<std::shared_ptr<int>> vec;
    void doWork() {
        std::weak_ptr<int> wp = vec[0];
        vec.push_back(std::make_shared<int>(5));
    }
    """
    issues = analyzer.analyze(code)
    assert len(issues) == 0


def test_safe_id_usage():
    analyzer = CppLifetimeAnalyzer()
    code = """
    #include <vector>
    class Book { public: int id; };
    std::vector<Book> inventory;

    int getBookId(int idx) {
        int bookId = inventory[idx].id;
        inventory.push_back(Book());
        return bookId;
    }
    """
    issues = analyzer.analyze(code)
    assert len(issues) == 0


# ---------------------------------------------------------------------------
# End-to-end unified review test using the FULL LibraryManager example
# ---------------------------------------------------------------------------

LIBRARY_MANAGER_FULL = r"""
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

class Book {
public:
    int id;
    std::string title;
    bool isBorrowed;
    Book(int id, const std::string& title) : id(id), title(title), isBorrowed(false) {}
};

class User {
public:
    std::string name;
    Book* currentBook;
    User(const std::string& name) : name(name), currentBook(nullptr) {}
};

class LibraryManager {
    std::vector<Book> inventory;

public:
    void addBook(int id, const std::string& title) {
        inventory.push_back(Book(id, title));
    }

    Book* findBookById(int id) {
        for (auto& book : inventory) {
            if (book.id == id) {
                return &book;
            }
        }
        return nullptr;
    }

    void removeBorrowedBooks() {
        inventory.erase(
            std::remove_if(inventory.begin(), inventory.end(),
                [](const Book& b) { return b.isBorrowed; }),
            inventory.end()
        );
    }

    std::string& getBookTitle(int index) {
        std::string localTitle = inventory[index].title;
        return localTitle;
    }

    void borrowBook(User& user, int bookId) {
        Book* book = findBookById(bookId);
        if (book) {
            book->isBorrowed = true;
            user.currentBook = book;
        }
    }

    void processBooks() {
        for (auto it = inventory.begin(); it != inventory.end(); ++it) {
            if (it->isBorrowed) {
                inventory.erase(it);
            }
        }
    }

    int getMissingReturn(int x) {
        if (x > 0) {
            return x;
        }
    }
};

int main() {
    LibraryManager lib;
    lib.addBook(1, "C++ Primer");
    lib.addBook(2, "Effective C++");

    User u1("Alice");
    User u2("Bob");

    lib.borrowBook(u1, 1);
    lib.borrowBook(u2, 2);

    lib.removeBorrowedBooks();
    std::cout << u1.currentBook->title << std::endl;

    lib.addBook(3, "New Book");
    std::cout << u2.currentBook->title << std::endl;

    Book* raw1 = new Book(10, "Raw");
    Book* raw2 = raw1;
    delete raw1;
    delete raw2;

    int result = lib.getMissingReturn(-1);
    std::cout << "Result: " << result << std::endl;

    return 0;
}
"""


def test_e2e_full_library_manager_has_erasure_finding():
    """End-to-end: the full LibraryManager source must produce a
    'Container erasure invalidates external pointer' finding that
    survives StaticAnalyzer + HybridEngine fusion."""
    sa = StaticAnalyzer()
    engine = HybridEngine()

    static_issues = sa.analyze(LIBRARY_MANAGER_FULL, "C++")
    normalised = engine.normalize(static_issues, "Static")
    fused = engine.fuse(normalised, [])

    erasure = [
        i for i in fused
        if "Container erasure" in i["description"]
        and "currentBook" in i["description"]
    ]
    assert len(erasure) >= 1, (
        f"Expected erasure finding mentioning currentBook; got: "
        f"{[i['description'] for i in fused]}"
    )


def test_e2e_full_library_manager_has_reallocation_finding():
    """End-to-end: the full LibraryManager source must produce a
    'Vector reallocation invalidates external pointer' finding that
    survives StaticAnalyzer + HybridEngine fusion."""
    sa = StaticAnalyzer()
    engine = HybridEngine()

    static_issues = sa.analyze(LIBRARY_MANAGER_FULL, "C++")
    normalised = engine.normalize(static_issues, "Static")
    fused = engine.fuse(normalised, [])

    realloc = [
        i for i in fused
        if "Vector reallocation" in i["description"]
        and "currentBook" in i["description"]
    ]
    assert len(realloc) >= 1, (
        f"Expected reallocation finding mentioning currentBook; got: "
        f"{[i['description'] for i in fused]}"
    )


def test_e2e_full_library_manager_keeps_double_free():
    """Existing double-free finding must still be present in the unified list."""
    sa = StaticAnalyzer()
    engine = HybridEngine()

    static_issues = sa.analyze(LIBRARY_MANAGER_FULL, "C++")
    normalised = engine.normalize(static_issues, "Static")
    fused = engine.fuse(normalised, [])

    double_free = [i for i in fused if "Double free" in i["description"]]
    assert len(double_free) == 1


def test_e2e_full_library_manager_keeps_raw_return():
    """Existing raw-return finding must still be present."""
    sa = StaticAnalyzer()
    engine = HybridEngine()

    static_issues = sa.analyze(LIBRARY_MANAGER_FULL, "C++")
    normalised = engine.normalize(static_issues, "Static")
    fused = engine.fuse(normalised, [])

    raw_ret = [i for i in fused if "Returning a raw pointer" in i["description"]]
    assert len(raw_ret) >= 1
