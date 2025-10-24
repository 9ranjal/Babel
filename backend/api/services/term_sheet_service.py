from typing import Dict, Any, Optional

class TermSheetService:
    """Service for generating term sheets from collected information"""

    def __init__(self):
        self.template = self._load_template()

    def _load_template(self) -> str:
        """Load the term sheet template"""
        return """
# {company_name} - {stage} Term Sheet

*This indicative term sheet ("Term Sheet") summarizes the principal terms, for negotiation purposes only, with respect to a potential investment by {lead_investor} in {company_name}. Save as otherwise specifically provided, nothing herein creates any legally binding obligation on the part of any party, nor shall any legally binding obligations arise unless and until the parties have executed definitive written agreements (the "Definitive Agreements") and obtained all requisite governmental, corporate, management and legal approvals.*

## Key Terms

| **Investee Company** | {company_name} (the "Company"), having its registered office at [insert registered office] |
| **Investor** | {lead_investor} and/or its affiliates (the "Investor") |
| **Founder/Sponsor(s)** | [Insert Name of Founder 1], [Insert Name of Founder 2], [Insert Name of Founder 3] (Individually, each a "Founder", collectively "Founders") |
| **Investment Amount and Investor Securities** | The Investor shall invest {investment_amount} into the Company through a primary investment at a pre-money valuation of {valuation} through a mix of compulsorily convertible cumulative preference shares ("CCCPS"), and a nominal number of equity shares; such that the Investor will own at least {equity_percentage} of the Company on a fully diluted post-money basis, post investment. |
| **ESOP** | An ESOP pool will be included in the pre-money valuation, equal to 15% of the share capital, on a post-money fully diluted basis. |
| **Voting Rights** | Each CCCPS and equity share shall carry one vote per share at all meetings of the shareholders. The Investor shall have the right to vote on an as-if-converted basis on all convertible securities held. |
| **Board of Directors** | The Investor shall be entitled to appoint {board_seats} nominee director(s) on the Board of the Company and 1 observer to attend all meetings of the Board in a non-voting capacity. |
| **Affirmative Rights** | The Investor will have standard affirmative consent rights (in relation to the Company and each subsidiary), including (but not limited to) in relation to the following: Economic rights such as approval rights on a change in the rights of securities, future fund-raise/ issue of capital, buy-backs/ redemption, dividends, etc; Governance rights such as approval rights on related party transactions, choice/change of auditors (Big 4 or any other mutually acceptable auditor), unusually large expenses or debt obligations to be undertaken by the company, change in constitutional documents, significant litigation; and Change in control, M&A, trade sale, asset sale, disposition or acquisition of any subsidiaries, changes in business etc. |
| **Liquidity Preference** | {liquidation_preference} on defined liquidity events. The preference shares issued to the investor shall be in senior to other existing classes of preference shares. Liquidity Events in the definitive agreements shall include IPO, sale resulting in change of control, M&A, winding up of the Company etc. |
| **Anti-Dilution Protection** | The Investor shall be entitled to anti-dilution protection on all future issuances at a price lower than the Investor's subscription price, on a {anti_dilution} basis. |
| **Use of Proceeds** | The Definitive Agreements will stipulate the permitted use of proceeds. |
| **Key Man Exclusivity, Non-Compete and Non-Solicit** | The Founder/Sponsor(s) and key employees shall devote all of their working time and effort to the Company, and shall not assist, advise or obtain any rights in any other business or commercial venture without obtaining the prior written approval of the Investor. The Founder/Sponsor(s) and key employees shall be bound by standard non-compete and non-solicit provisions, to be set out in the Definitive Agreements. |
| **Pre-emptive Rights** | The Investor shall have a right of first refusal to subscribe to its pro rata portion in any future fund raise. |
| **Exit Rights** | The Company and the Sponsor/Founder(s) will provide an exit acceptable to the Investor through an IPO or trade sale, within a period of 5 years ("Exit Period") from the date of closing of the investment. If the IPO is not completed within such time, the Investor shall have the right to require the Company and Sponsor/Founder(s) to provide an exit through sale to a third party buyer, or through a buyback / put, at fair market value (FMV). If such exit is also not completed within 6 months, the Investor shall have the right to drag all other shareholders to an exit. |
| **Share transfer Restrictions** | The Sponsor/Founder(s) shares will have a lock-in of 4 years. Investor's Right of First Refusal (ROFR): The Investor will have a right of first refusal on any sale or transfer of shares held by the Sponsor/Founder(s) and all other shareholders of the Company. Investor Tag Along Rights: Subject to the Investor's ROFR, the Investor will have the right to participate pro rata in any sale of shares to third parties by the Sponsor/Founder(s) or other shareholders, provided that if the Sponsor/Founder(s) shareholding will fall below 10% pursuant to the transaction, the Investor may tag along up to its entire shareholding. |
| **Termination of Sponsor/Founder(s)' Employment** | {vesting_schedule} The definitive agreements will specify the treatment of vested and unvested shares in the case of 'good leaver' and 'bad leaver' situations. |
| **Additional Rights** | The Investor will have all rights which any other existing or future investor (commensurate with the Investor's shareholding) in the Company may have. The Investor will also have standard information rights, including in relation to the receipt of audited and un-audited financial statements and quarterly MIS. In addition, Investors shall have standard inspection rights. |
| **Auditors** | The Company will retain an auditor acceptable to both the Investor and the Sponsor/Founder(s) within a period of 3 months from Closing. |
| **Closing Conditions** | The Closing of the transaction will be subject to (i) satisfactory completion of business, financial and legal due diligence and execution of legal documentation, (ii) no material adverse change, (iii) receipt by each party of all necessary governmental, corporate, management, and legal approvals, and (iv) any others as may be identified during the due diligence process (including restructuring of the Company and subsidiaries / group companies, if deemed necessary). |
| **Warranties** | The Sponsor/Founder(s) and Company will provide standard representations & warranties, and indemnities against the same. |
| **Assignment** | The Investor shall be entitled to freely transfer or otherwise assign its securities, rights and benefits (in full or in part) under the Definitive Agreements to any persons or third parties of its choosing. |
| **Confidentiality** | All the parties agree to keep all negotiations with the Investor on a confidential basis, including the existence and contents of this term sheet. |
| **Fees** | The Company agrees to reimburse expenses up to a maximum of $50,000 incurred by the Investor for this investment. Expenses will be reimbursed only upon successful consummation of the transaction. |
| **Exclusivity** | The Company agrees to negotiate the transaction contemplated above with the Investor on an exclusive basis for a period of {exclusivity_period} from the signing of acceptance of this term sheet, or such other extended time as may be mutually agreed between the parties. |
| **Governing law & Dispute Resolution** | This Term Sheet and the Definitive Agreements shall be governed by the laws of [Insert Country]. Disputes will be resolved by arbitration in Singapore as per the Rules of the Singapore International Arbitration Centre. Subject to the aforesaid, the courts at Singapore will have exclusive jurisdiction. |
| **Survival** | The paragraphs captioned "Confidentiality", "Fees", "Governing Law & Dispute Resolution", "Survival" and "Exclusivity" shall bind the parties and shall survive termination, withdrawal or expiry of this Term Sheet. |
| **Expiry of Proposal** | Save as otherwise provided elsewhere, this Term Sheet will automatically expire, and be of no further force and effect, if (i) the Investor has not received from the Company a copy of this letter acknowledged and agreed to by the Company on or before [5:00 PM IST on [date]]; or (ii) prior to any such receipt, the Investor orally or in writing, gives notice of withdrawal hereof. |

If the foregoing accurately describes the basis on which the undersigned are willing to proceed with regard to the proposed transaction, please indicate your approval by signing the copy of this term sheet and returning it to us.

**For {lead_investor}**

_________________________
Director                                                                                                                    Date:                

**Accepted and agreed**

By: _____________________________
Name: 
Date: For {company_name} _____________________________
Name:  Designation:  Date:   
"""

    def generate_term_sheet(self, data: Dict[str, Any]) -> str:
        """Generate term sheet from collected data"""
        # Extract data from the nested structure
        company = data.get('company', {})
        investors = data.get('investors', {})
        deal = data.get('deal', {})
        terms = data.get('terms', {})

        # Format the template with the collected data
        formatted_template = self.template.format(
            company_name=company.get('company_name', '[Company Name]'),
            stage=company.get('stage', '[Series/Seed/A/B/C]'),
            lead_investor=investors.get('lead_investor', '[Lead Investor]'),
            investment_amount=self._format_currency(investors.get('investment_amount', '[Amount]')),
            valuation=self._format_currency(investors.get('valuation', '[Valuation]')),
            equity_percentage=self._format_percentage(deal.get('equity_percentage', '[Percentage]')),
            board_seats=deal.get('board_seats', '[Number]'),
            liquidation_preference=deal.get('liquidation_preference', '1x, non-participating'),
            anti_dilution=deal.get('anti_dilution', 'broad-based weighted average'),
            vesting_schedule=terms.get('vesting_schedule', '100% of the Sponsor/Founder(s) shares will be subject to a 4 year vesting period, with a 1-year cliff (i.e., vesting of 25% shall happen at the end of such 1-year period), with vesting being on a monthly basis thereafter.'),
            exclusivity_period=terms.get('exclusivity_period', '60 days')
        )

        return formatted_template

    def _format_currency(self, amount: str) -> str:
        """Format currency amount"""
        if not amount or amount == '[Amount]' or amount == '[Valuation]':
            return amount
        if isinstance(amount, str) and ('$' in amount or 'USD' in amount or 'INR' in amount):
            return amount
        return f"${amount}"

    def _format_percentage(self, percentage: str) -> str:
        """Format percentage"""
        if not percentage or percentage == '[Percentage]':
            return percentage
        if isinstance(percentage, str) and '%' in percentage:
            return percentage
        return f"{percentage}%"

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the collected data"""
        company = data.get('company', {})
        investors = data.get('investors', {})
        deal = data.get('deal', {})
        terms = data.get('terms', {})

        # Set defaults for missing required fields
        defaults = {
            'company': {
                'company_name': '[Company Name]',
                'stage': '[Series/Seed/A/B/C]',
                'industry': '[Industry]',
                'revenue': '[Revenue]'
            },
            'investors': {
                'lead_investor': '[Lead Investor]',
                'investment_amount': '[Amount]',
                'valuation': '[Valuation]'
            },
            'deal': {
                'equity_percentage': '[Percentage]',
                'liquidation_preference': '1x, non-participating',
                'board_seats': '[Number]',
                'anti_dilution': 'broad-based weighted average'
            },
            'terms': {
                'exclusivity_period': '60 days',
                'vesting_schedule': '4 years, 1 year cliff',
                'drag_along': 'Yes',
                'tag_along': 'Yes'
            }
        }

        # Merge with defaults
        for section, default_values in defaults.items():
            if section not in data:
                data[section] = default_values
            else:
                for key, default_value in default_values.items():
                    if key not in data[section] or not data[section][key]:
                        data[section][key] = default_value

        return data

# Global instance
term_sheet_service = TermSheetService()
