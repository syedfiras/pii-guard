export const PRESETS = {
  all: {
    label: 'All Combined',
    text: 'Hi, I am Ravi Kumar. My email is ravi.k@test.com, call me on 9876543210. PAN ABCDE1234F, Aadhaar 2344 5678 9012, credit card 4111 1111 1111 1111.',
  },
  email: { label: 'Email', text: 'Please send the invoice to priya.sharma@test.com urgently.' },
  phone: { label: 'Phone', text: 'Call me back on +91-98765 43210 tomorrow morning.' },
  pan: { label: 'PAN', text: 'My PAN for KYC is BNZPM5678K, please verify.' },
  aadhaar: { label: 'Aadhaar', text: 'Aadhaar number 2344 5678 9012 for address proof.' },
  debit: { label: 'Debit card', text: 'My debit card 5555 5555 5555 4444 for the payment.' },
  credit: { label: 'Credit card', text: 'Charge my credit card 4111 1111 1111 1111 for Rs. 2,500.' },
  upi: { label: 'UPI', text: 'Send Rs. 500 to priya@okhdfcbank today.' },
  name: { label: 'Name', text: 'Ravi Kumar from Mumbai called about invoice 48210.' },
}

export const TYPE_HELP = {
  EMAIL: 'like name@mail.com',
  PHONE: '10-digit Indian mobile',
  PAN: 'LIKE THIS: ABCDE1234F',
  AADHAAR: '12-digit number',
  CARD: 'card number with correct check digit',
  UPI_ID: 'like name@okhdfcbank',
  PASSPORT_IN: 'like N1234567',
  DATE: 'dates like 12/05/1998',
  PERSON: 'names (computer guesses)',
  LOCATION: 'places (computer guesses)',
}

export const ALL_KINDS = Object.keys(TYPE_HELP)

export const LIMITS = [
  'Without strict mode, Aadhaar checking can mistake other long numbers for Aadhaar.',
  'Small-letter PAN (like abcde1234f) is not caught — only CAPITAL letters.',
  'Phone checking follows Indian mobile rules (+91, starting with 6–9).',
  'Cards need the correct check number; wrong ones are ignored. CVV/expiry codes are not covered.',
  'Names and other languages are not covered yet.',
]
