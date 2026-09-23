import pytest
from app.ai.category_classifier import CategoryClassifier
from create_incidents import CATEGORIES_ISSUES

def test_category_classifier_seed_issues():
    """Verify that CategoryClassifier accurately categorizes all 35 issues from create_incidents."""
    for expected_cat, issues in CATEGORIES_ISSUES.items():
        for issue in issues:
            detected = CategoryClassifier.classify(issue)
            assert detected == expected_cat, f"MISMATCH for '{issue}': expected {expected_cat}, got {detected}"

def test_category_classifier_real_world_samples():
    # Database
    assert CategoryClassifier.classify("Oracle DB connection timeout on SAP ORA01 (P1)") == "database"
    assert CategoryClassifier.classify("Tablespace full on PostgreSQL cluster") == "database"
    assert CategoryClassifier.classify("HikariCP connection pool exhausted after 30000ms") == "database"

    # Hardware
    assert CategoryClassifier.classify("Laptop screen flickering and trackpad unresponsive") == "hardware"
    assert CategoryClassifier.classify("Docking station not charging ThinkPad and HDMI dead") == "hardware"
    assert CategoryClassifier.classify("Floor 4 printer paper jam and toner empty") == "hardware"

    # Network
    assert CategoryClassifier.classify("Corporate VPN tunnel dropped for remote workers") == "network"
    assert CategoryClassifier.classify("High packet loss on edge router Cisco 9300") == "network"
    assert CategoryClassifier.classify("Cannot ping internal DNS server 10.0.1.5") == "network"

    # Software
    assert CategoryClassifier.classify("Customer Portal throwing HTTP 500 Internal Server Error") == "software"
    assert CategoryClassifier.classify("SAP monthly ledger reconciliation job crashed") == "software"
    assert CategoryClassifier.classify("Visio desktop license expired error message") == "software"

    # Inquiry / Help
    assert CategoryClassifier.classify("How to request a new monitor?") == "inquiry"
    assert CategoryClassifier.classify("Password reset request for remote contractor") == "inquiry"
    assert CategoryClassifier.classify("When is the next company holiday?") == "inquiry"
    assert CategoryClassifier.classify("Need access to the new project repository") == "inquiry"

def test_category_classifier_display_labels():
    assert CategoryClassifier.get_display_label("database") == "Database"
    assert CategoryClassifier.get_display_label("hardware") == "Hardware"
    assert CategoryClassifier.get_display_label("inquiry") == "Inquiry / Help"
    assert CategoryClassifier.get_display_label("network") == "Network"
    assert CategoryClassifier.get_display_label("software") == "Software"

def test_category_classifier_normalization():
    assert CategoryClassifier.normalize("Database") == "database"
    assert CategoryClassifier.normalize("Inquiry / Help") == "inquiry"
    assert CategoryClassifier.normalize("Network") == "network"
    assert CategoryClassifier.normalize("Software") == "software"
    assert CategoryClassifier.normalize("Hardware") == "hardware"
    assert CategoryClassifier.normalize("UNKNOWN") is None
