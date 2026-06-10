export default function SimInput({ className, onChange, ...inputProps }) {
  return (
    <p className={className}>
      <label htmlFor="tleFile">Choose TLE file</label>
      <input
        {...inputProps}
        id="tleFile"
        type="file"
        accept=".txt"
        name="tleFile"
        required
        onChange={onChange}
      />
    </p>
  );
}
