from lead_gen.server import app as app

# async def main():
#     await database.on_startup()

#     print("[green]Welcome to the Lead cold email generation tool![/green]")

#     hunter_key = credentials.get_credentials("hunter")
#     if hunter_key is None:
#         hunter_key = input("Enter your Hunter API key: ")
#         credentials.set_credentials("hunter", hunter_key)

#     openai_key = credentials.get_credentials("openai")
#     if openai_key is None:
#         openai_key = input("Enter your OpenAI API key: ")
#         credentials.set_credentials("openai", openai_key)

#     print("Getting Hunter leads...")

#     hunter.login(hunter_key)
#     leads = await hunter.list_leads()

#     for lead in leads:
#         company, _ = await Company.get_or_create(
#             name=lead["company"],
#             defaults={
#                 "name": lead["company"],
#                 "website": lead["website"],
#             },
#         )
#         person, _ = await Person.get_or_create(
#             id_hunter=lead["id"],
#             defaults={
#                 "id_hunter": lead["id"],
#                 "name": f"{lead["first_name"]} {lead["last_name"]}",
#                 "email": lead["email"],
#                 "company": company,
#             }
#         )

#     print(f"Added {len(leads)} leads to the database.")
#     await database.on_shutdown()


# def run():
#     asyncio.run(main())
