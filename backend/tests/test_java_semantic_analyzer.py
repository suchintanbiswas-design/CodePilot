import pytest
from app.engine.java_analyzer import JavaSemanticAnalyzer
from app.engine.static_analyzer import StaticAnalyzer
from app.engine.hybrid_engine import HybridEngine


# ---------------------------------------------------------------------------
# The full BankManager example
# ---------------------------------------------------------------------------

BANK_MANAGER_CODE = r"""
import java.util.ArrayList;
import java.util.List;

class Account {
    private String accountNumber;
    private double balance;
    private String ownerName;

    public Account(String accountNumber, double initialBalance, String owner) {
        this.accountNumber = accountNumber;
        this.balance = initialBalance;
        this.ownerName = owner;
    }

    public String getAccountNumber() { return accountNumber; }
    public double getBalance() { return balance; }
    public String getOwnerName() { return ownerName; }

    public void deposit(double amount) {
        balance += amount;
    }

    public boolean withdraw(double amount) {
        if (amount > balance) return false;
        balance -= amount;
        return true;
    }

    public boolean equals(Account other) {
        return this.accountNumber == other.accountNumber;
    }
}

class Customer {
    private String name;
    private String password;
    private List<Account> accounts;

    public Customer(String name, String password) {
        this.name = name;
        this.password = password;
    }

    public boolean authenticate(String inputPassword) {
        return password == inputPassword;
    }

    public String getName() { return name; }
    public List<Account> getAccounts() { return accounts; }
}

class BankManager {
    private List<Account> masterAccountList = new ArrayList<>();
    private List<Customer> customers = new ArrayList<>();

    public void addAccount(Account acc) {
        masterAccountList.add(acc);
    }

    public Account findAccount(String accountNumber) {
        for (int i = 0; i <= masterAccountList.size(); i++) {
            Account acc = masterAccountList.get(i);
            if (acc.getAccountNumber() == accountNumber) {
                return acc;
            }
        }
        return null;
    }

    public void removeAllAccounts(Customer customer) {
        for (Account acc : masterAccountList) {
            if (customer.getAccounts().contains(acc)) {
                masterAccountList.remove(acc);
            }
        }
    }

    public double getTotalBalance() {
        double balanceSum = 0.1 + 0.2;
        for (int i = 0; i < masterAccountList.size(); i++) {
            balanceSum += masterAccountList.get(i).getBalance();
        }
        return balanceSum;
    }

    public void processTransfer(String fromAccNum, String toAccNum, double amount) {
        Account from = findAccount(fromAccNum);
        Account to = findAccount(toAccNum);

        switch (from.getBalance() > amount ? 1 : 0) {
            case 1:
                from.withdraw(amount);
                to.deposit(amount);
            case 0:
                System.out.println("Transfer failed or completed");
        }
    }
}
"""


# ---------------------------------------------------------------------------
# Unit-level JavaSemanticAnalyzer tests
# ---------------------------------------------------------------------------

class TestEqualsContract:
    """Rule 1: equals() overload + missing hashCode()."""

    def test_equals_overload_detected(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Account {
            private String id;
            public boolean equals(Account other) {
                return this.id.equals(other.id);
            }
        }
        """
        issues = analyzer.analyze(code)
        eq_issues = [i for i in issues if "equals(Account) overloads" in i["description"]]
        assert len(eq_issues) == 1
        assert "hashCode() is missing" in eq_issues[0]["description"]
        assert eq_issues[0]["severity"] == "High"

    def test_proper_override_not_flagged(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Account {
            private String id;

            @Override
            public boolean equals(Object other) {
                if (!(other instanceof Account)) return false;
                return this.id.equals(((Account) other).id);
            }

            @Override
            public int hashCode() {
                return id.hashCode();
            }
        }
        """
        issues = analyzer.analyze(code)
        eq_issues = [i for i in issues if "equals" in i.get("description", "").lower() and "overload" in i.get("description", "").lower()]
        assert len(eq_issues) == 0

    def test_equals_object_with_hashcode_not_flagged(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Foo {
            public boolean equals(Object o) { return true; }
            public int hashCode() { return 42; }
        }
        """
        issues = analyzer.analyze(code)
        eq_issues = [i for i in issues if "overloads" in i.get("description", "")]
        assert len(eq_issues) == 0


class TestStringReferenceComparison:
    """Rule 2: String == String detection."""

    def test_string_eq_in_authenticate(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Customer {
            private String password;
            public boolean authenticate(String inputPassword) {
                return password == inputPassword;
            }
        }
        """
        issues = analyzer.analyze(code)
        str_issues = [i for i in issues if "String comparison" in i["description"]]
        assert len(str_issues) == 1
        assert str_issues[0]["severity"] == "High"

    def test_string_eq_in_findAccount(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class BankManager {
            public Account findAccount(String accountNumber) {
                Account acc = getFirst();
                if (acc.getAccountNumber() == accountNumber) {
                    return acc;
                }
                return null;
            }
        }
        """
        issues = analyzer.analyze(code)
        str_issues = [i for i in issues if "String comparison" in i["description"]]
        assert len(str_issues) == 1

    def test_proper_string_equals_not_flagged(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Foo {
            public boolean check(String a, String b) {
                return a.equals(b);
            }
        }
        """
        issues = analyzer.analyze(code)
        str_issues = [i for i in issues if "String comparison" in i.get("description", "")]
        assert len(str_issues) == 0

    def test_primitive_comparison_not_flagged(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Foo {
            public boolean check(int a) {
                if (a == 1) return true;
                int b = 5;
                return a != b;
            }
        }
        """
        issues = analyzer.analyze(code)
        str_issues = [i for i in issues if "String comparison" in i.get("description", "")]
        assert len(str_issues) == 0


class TestFloatingPointCurrency:
    """Rule 3: Floating-point for financial values."""

    def test_double_balance_field(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Account {
            private double balance;
        }
        """
        issues = analyzer.analyze(code)
        fp_issues = [i for i in issues if "floating-point" in i["description"].lower()]
        assert len(fp_issues) == 1
        assert "balance" in fp_issues[0]["description"]
        assert fp_issues[0]["severity"] == "Medium"

    def test_double_balanceSum_calculation(self):
        analyzer = JavaSemanticAnalyzer()
        code = """
        class BankManager {
            public double getTotalBalance() {
                double balanceSum = 0.1 + 0.2;
                return balanceSum;
            }
        }
        """
        issues = analyzer.analyze(code)
        fp_issues = [i for i in issues if "floating-point" in i["description"].lower() and "balanceSum" in i["description"]]
        assert len(fp_issues) >= 1

    def test_scientific_double_not_flagged(self):
        """Non-financial calculations using double should not be flagged."""
        analyzer = JavaSemanticAnalyzer()
        code = """
        class Physics {
            public double calculateDistance(double x, double y) {
                double distance = Math.sqrt(x * x + y * y);
                return distance;
            }
        }
        """
        issues = analyzer.analyze(code)
        fp_issues = [i for i in issues if "floating-point" in i.get("description", "").lower() and "financial" in i.get("description", "").lower()]
        assert len(fp_issues) == 0

    def test_bigdecimal_not_flagged(self):
        """Using BigDecimal for financial values should not trigger the warning."""
        analyzer = JavaSemanticAnalyzer()
        code = """
        import java.math.BigDecimal;
        class Account {
            private BigDecimal balance;
            public void deposit(BigDecimal amount) {
                balance = balance.add(amount);
            }
        }
        """
        issues = analyzer.analyze(code)
        fp_issues = [i for i in issues if "floating-point" in i.get("description", "").lower()]
        assert len(fp_issues) == 0


# ---------------------------------------------------------------------------
# End-to-end integration tests using the full BankManager example
# ---------------------------------------------------------------------------

class TestE2EBankManagerPipeline:
    """Verify that findings survive the full StaticAnalyzer -> HybridEngine pipeline."""

    def _get_fused_issues(self):
        sa = StaticAnalyzer()
        engine = HybridEngine()
        static_issues = sa.analyze(BANK_MANAGER_CODE, "Java")
        normalised = engine.normalize(static_issues, "Static")
        return engine.fuse(normalised, [])

    def test_equals_overload_in_fused(self):
        fused = self._get_fused_issues()
        eq_issues = [i for i in fused if "equals(Account) overloads" in i["description"]]
        assert len(eq_issues) == 1, (
            f"Expected equals overload finding; got: "
            f"{[i['description'] for i in fused if 'equals' in i.get('description','').lower()]}"
        )

    def test_hashcode_missing_in_fused(self):
        fused = self._get_fused_issues()
        eq_issues = [i for i in fused if "hashCode() is missing" in i["description"]]
        assert len(eq_issues) == 1

    def test_string_eq_authenticate_in_fused(self):
        fused = self._get_fused_issues()
        str_issues = [i for i in fused if "String comparison" in i["description"]]
        # authenticate + equals body + findAccount = 3 String == findings
        assert len(str_issues) >= 2

    def test_string_eq_findAccount_in_fused(self):
        fused = self._get_fused_issues()
        str_issues = [i for i in fused if "String comparison" in i["description"]]
        # Verify at least one is on the findAccount line (line ~64)
        find_account_issues = [i for i in str_issues if i["line_number"] > 60]
        assert len(find_account_issues) >= 1

    def test_double_balance_in_fused(self):
        fused = self._get_fused_issues()
        fp_issues = [i for i in fused if "balance" in i.get("description", "") and "floating-point" in i.get("description", "").lower()]
        assert len(fp_issues) >= 1

    def test_double_balanceSum_in_fused(self):
        fused = self._get_fused_issues()
        fp_issues = [i for i in fused if "balanceSum" in i.get("description", "") and "floating-point" in i.get("description", "").lower()]
        assert len(fp_issues) >= 1

    def test_total_correctness_issues(self):
        fused = self._get_fused_issues()
        correctness = [i for i in fused if i.get("rule_type") == "Correctness"]
        # At least 6: 1 equals + 3 string== + 2 float
        assert len(correctness) >= 6
