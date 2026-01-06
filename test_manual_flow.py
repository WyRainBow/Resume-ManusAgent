#!/usr/bin/env python3
"""
Manual test to observe the actual flow with detailed error capture.
This test will wait longer and capture all console messages including errors.
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright


async def manual_test():
    """Manual test with extended observation"""
    print("=" * 100)
    print("MANUAL RESUME FLOW TEST - Extended Observation")
    print("=" * 100)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()

        all_messages = []
        errors = []
        agent_errors = []

        def handle_console(msg):
            timestamp = datetime.now().isoformat()
            text = msg.text

            all_messages.append({
                "timestamp": timestamp,
                "type": msg.type,
                "text": text
            })

            # Capture errors
            if msg.type == "error":
                errors.append({
                    "timestamp": timestamp,
                    "text": text
                })
                print(f"  [ERROR] {text}")

            # Capture agent errors specifically
            if "agent_error" in text:
                agent_errors.append({
                    "timestamp": timestamp,
                    "text": text
                })
                print(f"  [AGENT ERROR] {text}")

            # Log tool calls
            if any(kw in text.lower() for kw in ["tool_call", "cv_reader", "cv_analyzer"]):
                print(f"  [TOOL] {text[:150]}")

        page.on("console", handle_console)

        try:
            # Navigate
            print("[1/4] Navigating to http://localhost:5173...")
            await page.goto("http://localhost:5173", wait_until="domcontentloaded")
            await asyncio.sleep(3)

            # Send greeting
            print("[2/4] Sending greeting '你好'...")
            textarea = await page.wait_for_selector("textarea")
            await textarea.fill("你好")
            await asyncio.sleep(0.5)
            await textarea.press("Enter")
            await asyncio.sleep(5)

            # Load resume
            print("[3/4] Loading resume...")
            await asyncio.sleep(2)
            await page.fill("textarea", "加载简历/Users/wy770/Resume_OpenMauns/OpenManus/app/docs/韦宇_简历.md")
            await asyncio.sleep(0.5)
            await page.press("textarea", "Enter")
            await asyncio.sleep(10)

            # Ask question
            print("[4/4] Asking question '我是哪个大学的'...")
            await asyncio.sleep(2)
            await page.fill("textarea", "我是哪个大学的")
            await asyncio.sleep(0.5)
            await page.press("textarea", "Enter")

            # Wait and observe for 40 seconds
            print("\n[OBSERVATION] Monitoring for 40 seconds...")
            print("-" * 100)

            for i in range(40):
                await asyncio.sleep(1)
                if i % 5 == 0:
                    print(f"  Elapsed: {i}s")

            # Take final screenshot
            await page.screenshot(path="test_manual_final.png", full_page=True)
            print("\n[SCREENSHOT] Saved test_manual_final.png")

        finally:
            # Analysis
            print("\n" + "=" * 100)
            print("ANALYSIS")
            print("=" * 100)

            print(f"\nTotal console messages: {len(all_messages)}")
            print(f"Total errors: {len(errors)}")
            print(f"Agent errors: {len(agent_errors)}")

            # Find tool calls
            tool_calls = [msg for msg in all_messages if "tool_call" in msg.get("text", "")]
            print(f"\nTool calls detected: {len(tool_calls)}")
            for tc in tool_calls:
                print(f"  - {tc['text'][:150]}")

            # Show agent errors in detail
            if agent_errors:
                print("\n" + "-" * 100)
                print("AGENT ERRORS (CRITICAL):")
                print("-" * 100)
                for ae in agent_errors:
                    print(f"\n  Time: {ae['timestamp']}")
                    print(f"  Error: {ae['text']}")

            # Save detailed log
            log = {
                "timestamp": datetime.now().isoformat(),
                "total_messages": len(all_messages),
                "errors": errors,
                "agent_errors": agent_errors,
                "tool_calls": tool_calls,
                "all_messages": all_messages[-100:]  # Last 100 messages
            }

            with open("test_manual_log.json", "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)

            print(f"\n[LOG] Saved test_manual_log.json")
            print("=" * 100)

            await asyncio.sleep(2)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(manual_test())
