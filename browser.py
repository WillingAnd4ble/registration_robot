from playwright.sync_api import sync_playwright
import pandas


data = pandas.read_csv("data/data.csv").fillna("Undefined")

def login(username: str, password: str) -> None:
    page.goto("https://parabank.parasoft.com/parabank/login.htm")
    page.wait_for_load_state("networkidle")
    
def register(firstName: str, lastName: str, address: str, city: str, state: str, zipCode: str, phoneNumber: str, ssn: str, username: str, password: str) -> None:
   page.goto("https://parabank.parasoft.com/parabank/register.htm")
   page.fill("[name='customer.firstName']", firstName)
   page.fill("[name='customer.lastName']", lastName)
   page.fill("[name='customer.address.street']", address)
   page.fill("[name='customer.address.city']", city)
   page.fill("[name='customer.address.state']", state)
   page.fill("[name='customer.address.zipCode']", zipCode)
   page.fill("[name='customer.phoneNumber']", phoneNumber)
   page.fill("[name='customer.ssn']", ssn)
   page.fill("[name='customer.username']", username) 
   page.fill("[name='customer.password']", password)
   page.fill("[name='repeatedPassword']", password)
   page.click("input[value='Register']") 
   page.wait_for_load_state("networkidle")
   if page.locator("span.error").count() > 0:
      page.fill("[name='username']", username)
      page.fill("[name='password']", password)
      page.click("input[value='Log In']")

def open_account(account_type: str) -> str:
   page.goto("https://parabank.parasoft.com/parabank/openaccount.htm")
   type_value = "0" if account_type.upper() == "CHECKING" else "1"
   page.select_option("select#type", type_value)
   page.select_option("select#fromAccountId", index=0)
   page.click("input[value='Open New Account']")
   page.wait_for_load_state("networkidle")
   new_id = page.locator("#newAccountId").inner_text()
   return new_id

def ask_loan(amount: str, down_payment: str, from_account_id: str) -> dict:
   page.goto("https://parabank.parasoft.com/parabank/requestloan.htm")
   page.fill("#amount",str( amount))
   page.fill("#downPayment", str(down_payment))
   page.select_option("#fromAccountId", from_account_id)
   page.click("input[value='Apply Now']")
   page.wait_for_load_state("networkidle")
   return { "provider": page.locator("#loanProviderName").inner_text(),
        "date": page.locator("#responseDate").inner_text(),
        "status": page.locator("#loanStatus").inner_text(), 
   }


def logout() -> None:
    page.click("a[href*='logout']")
    page.wait_for_load_state("networkidle")
    
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    loan_info = {}
    id = ""
    loan_amount = 10000
    report = []
    context = browser.new_context(record_video_dir="gifs/")
    page = context.new_page()
    for _, row in data.iterrows():
      register(row["FirstName"], row["LastName"], row["Address"],
            row["City"], row["State"], str(row["ZipCode"]),
            str(row["PhoneNumber"]), str(row["SSN"]),
            row["Username"], row["Password"])
      id = open_account(row["AccountType"])
      try:
         down_payment = round(float(row["InitialDeposit"]) * 0.2, 2)
         loan_info = ask_loan(loan_amount, down_payment, id)
      except (ValueError, TypeError):
         print(f"Skipping {row['Username']} — invalid InitialDeposit: {row['InitialDeposit']}")
         loan_info = {"provider": "N/A", "date": "N/A", "status": "Failed - Invalid InitialDeposit"}
         down_payment = "N/A"
      report.append({
        "FirstName": row["FirstName"],
        "LastName": row["LastName"],
        "Username": row["Username"],
        "DOB": row["DOB"],
        "DebitCard": row["DebitCard"],
        "CVV": row["CVV"],
        "AccountID": id,
        "LoanProvider": loan_info["provider"],
        "LoanDate": loan_info["date"],
        "LoanAmount_EUR": round(10000 * 0.87, 2),
        "LoanDownPayment_EUR": round(down_payment * 0.87, 2) if down_payment != "N/A" else "N/A", 
        "LoanStatus": loan_info["status"],
    })
      logout()
      print(id)
      print(loan_info["status"])
    pandas.DataFrame(report).to_excel("report.xlsx", index=False)  
    context.close()
    browser.close()