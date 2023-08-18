routes in auth.py are used for basic authentications which can be used for all user grades(i.e admin, providers, patient)
auth.py contains:
    1. createAccount - used to create accounts for users.
    2. signin - used to log users in.
    3. emailCheck -which is used to check if the email used provided during authentication already previously exists.
    4. emailVerification -  is used to send verification links to user's mails which are used for verifying  the users.
    5. confirmEmail - is used to create verification links to be sent to users emails provided during account creation.
    6. sendOTP - is used to send OTPs to provided emails.
    7. verifyOTP - is used to verify the OTPs sent to the mails.
    8. postPassword - is used to update passwords with new passwords provided.
