export default function SimInput({ className, htmlFor, ...props }) {
  return (
    <p className={className}>
      <label htmlFor="tleFile">Choose TLE file</label>
      <input
        id="tleFile"
        type="file"
        accept=".txt"
        name="tleFile"
        required
        onChange={handleUserTLE}
      />
    </p>
  );
}
