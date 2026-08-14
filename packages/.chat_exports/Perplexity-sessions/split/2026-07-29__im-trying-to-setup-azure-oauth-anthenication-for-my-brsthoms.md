---
title: "I'm trying to setup azure oauth anthenication for my brsthomson@hotmail account: unauthorized_client: The client does no"
date: "2026-07-29"
mode: "COPILOT"
uuid: "0d5a66cd-c2bb-4363-ba3d-b4da8b0ce5f6"
entry_count: 1
---

## Human

I'm trying to setup azure oauth anthenication for my brsthomson@hotmail account: unauthorized_client: The client does not exist or is not enabled for consumers. If you are the application developer, configure a new application through the App Registrations in the Azure Portal at [https://go.microsoft.com/fwlink/?linkid=2083908](https://go.microsoft.com/fwlink/?linkid=2083908).

## Assistant

That error usually means the app registration is configured for work/school accounts only, while `brsthomson@hotmail.com` is a personal Microsoft account, so Microsoft rejects it as a consumer sign-in. Hotmail accounts are explicitly treated as personal Microsoft accounts, and the app must support either **Personal accounts only** or **Any Entra ID tenant + Personal Microsoft accounts** for that login to work.[1][2]

## What the error means

Your premise should be challenged a bit: this is probably **not** a problem with your Hotmail account itself. It is usually a configuration issue in the Azure / Microsoft Entra app registration, specifically the app’s supported account type or sign-in audience.[2][1]

Microsoft’s app registration options distinguish between organizational accounts and personal Microsoft accounts, and Hotmail falls in the personal-account category. If the app was registered as single-tenant or organizational-only, a Hotmail sign-in can trigger `unauthorized_client: The client does not exist or is not enabled for consumers`.[1][2]

## Likely fixes

If **you own the app registration**, go to Microsoft Entra admin center, open **Entra ID > App registrations > your app**, then check **Supported account types**. For your Hotmail account, the app must be registered as either **Any Entra ID Tenant + Personal Microsoft accounts** or **Personal accounts only**.[1]

If the app already exists, you can also change it through the manifest by setting `signInAudience` to `AzureADandPersonalMicrosoftAccount` or `PersonalMicrosoftAccount`. Microsoft documents those exact manifest values and their meanings.[2]

- `AzureADMyOrg` = org only, will not work for Hotmail.[2]
- `AzureADMultipleOrgs` = work/school accounts across tenants, still not enough for Hotmail.[2]
- `AzureADandPersonalMicrosoftAccount` = work/school plus Hotmail/Outlook/Live/Xbox accounts.[2]
- `PersonalMicrosoftAccount` = personal Microsoft accounts only.[2]

## Important checks

Make sure you are creating or editing the app registration in the **correct tenant**. Microsoft says app registrations are created inside a tenant, and you must switch to the right tenant before creating or editing the app.[1][2]

Also confirm you are using the correct **Application (client) ID** from that registration, because the same error can appear when the client ID points to the wrong app or wrong tenant context. Microsoft’s registration guide identifies the client ID as the key identifier your app uses during authentication.[1]

## Practical path

1. Sign in to the [Microsoft Entra admin center](https://entra.microsoft.com/) with an account that can manage app registrations.[1]
2. Switch to the tenant where the app lives.[1][2]
3. Open **App registrations** and select the app.[2][1]
4. Set supported account type to **Any Entra ID Tenant + Personal Microsoft accounts** if you want both business and Hotmail users, or **Personal accounts only** if this is just for your Hotmail account.[1][2]
5. Recheck the client ID, redirect URI, and any code or config using that app. The supported-account fix is the main issue here, but mismatched client IDs can also block sign-in.[1]

## Confidence

**FACT:** Hotmail is a personal Microsoft account, and Azure / Entra apps must explicitly support personal Microsoft accounts to allow that login.[2][1]

**LIKELY:** Your app is currently single-tenant or org-only, or you are using a client ID from an app registration that is not enabled for consumer accounts.[3][2][1]

**UNCERTAINTY:** I cannot tell from the error alone whether the root cause is only the supported account type, the wrong tenant, or the wrong client ID. Those are the three main possibilities from the documentation and support guidance.[2][1]

Paste your current app registration settings — supported account type, authority/tenant URL, redirect URI, and the code or config block you’re using — and I’ll tell you the minimal change needed.
