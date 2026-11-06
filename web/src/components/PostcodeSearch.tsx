"use client";

import { useId, useRef, useState, type FormEvent } from "react";
import { ApiError, lookupPostcode, type ApiProblem } from "@/lib/api/client";
import { isInsideLondon, type Position } from "@/lib/geo";
import { normalisePostcode } from "@/lib/postcode";
import styles from "./PostcodeSearch.module.css";

export interface FoundPostcode extends Position {
  postcode: string;
}

const PROBLEMS: Record<ApiProblem, string> = {
  invalid: "Enter a full UK postcode, such as SW1A 2AA.",
  not_found: "We couldn't find that postcode. Check it and try again.",
  busy: "There have been too many searches in a short time. Wait a minute, then try again.",
  unavailable: "Postcode search isn't working right now. Try again in a few minutes.",
};

/** Finds a postcode's position. The postcode goes to PerilMap's API and is never saved. */
export function PostcodeSearch({ onFound }: { onFound: (found: FoundPostcode) => void }) {
  const id = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const requestRef = useRef<AbortController | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [finding, setFinding] = useState(false);

  function fail(message: string) {
    setError(message);
    inputRef.current?.focus();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = inputRef.current?.value ?? "";
    if (!text.trim()) {
      fail("Enter a postcode.");
      return;
    }
    const postcode = normalisePostcode(text);
    if (!postcode) {
      fail(PROBLEMS.invalid);
      return;
    }
    if (inputRef.current) {
      inputRef.current.value = postcode;
    }

    requestRef.current?.abort();
    const request = new AbortController();
    requestRef.current = request;
    setError(null);
    setFinding(true);
    try {
      const found = await lookupPostcode(postcode, request.signal);
      if (!isInsideLondon(found)) {
        fail(`${found.postcode} is outside Greater London. PerilMap only covers London so far.`);
        return;
      }
      onFound({ postcode: found.postcode, latitude: found.latitude, longitude: found.longitude });
    } catch (caught) {
      if (request.signal.aborted) {
        return;
      }
      fail(PROBLEMS[caught instanceof ApiError ? caught.problem : "unavailable"]);
    } finally {
      if (requestRef.current === request) {
        setFinding(false);
      }
    }
  }

  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <label htmlFor={id} className={styles.label}>
        Postcode
      </label>
      <p id={hintId} className={styles.hint}>
        For example, SW1A 2AA
      </p>
      {error && (
        <p id={errorId} className={styles.error}>
          {error}
        </p>
      )}
      <div className={styles.row}>
        <input
          ref={inputRef}
          id={id}
          name="postcode"
          className={styles.input}
          autoComplete="postal-code"
          autoCapitalize="characters"
          spellCheck={false}
          enterKeyHint="search"
          maxLength={16}
          aria-describedby={error ? `${hintId} ${errorId}` : hintId}
          aria-invalid={error ? true : undefined}
        />
        <button type="submit" className={styles.submit} disabled={finding}>
          {finding ? "Finding" : "Find postcode"}
        </button>
      </div>
      <p className="visually-hidden" role="status">
        {finding ? "Finding the postcode" : ""}
      </p>
    </form>
  );
}
