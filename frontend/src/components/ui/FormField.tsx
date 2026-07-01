import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

type BaseProps = {
  label: string;
  hint?: string;
  error?: string;
  children?: ReactNode;
};

type InputFieldProps = BaseProps & {
  as?: "input";
} & InputHTMLAttributes<HTMLInputElement>;

type TextareaFieldProps = BaseProps & {
  as: "textarea";
} & TextareaHTMLAttributes<HTMLTextAreaElement>;

export function FormField(props: InputFieldProps | TextareaFieldProps) {
  const { label, hint, error } = props;
  const sharedClassName = `form-field__control${error ? " form-field__control--error" : ""}`.trim();

  return (
    <label className="form-field">
      <span className="form-field__label">{label}</span>
      {props.as === "textarea" ? renderTextarea(props, sharedClassName) : renderInput(props, sharedClassName)}
      {error ? (
        <span className="form-field__error">{error}</span>
      ) : hint ? (
        <span className="form-field__hint">{hint}</span>
      ) : null}
    </label>
  );
}

function renderInput(props: InputFieldProps, sharedClassName: string) {
  const { label, hint, error, children: _children, as: _as, className, ...rest } = props;
  return <input {...rest} className={`${sharedClassName} ${className ?? ""}`.trim()} />;
}

function renderTextarea(props: TextareaFieldProps, sharedClassName: string) {
  const { label, hint, error, children: _children, as: _as, className, ...rest } = props;
  return <textarea {...rest} className={`${sharedClassName} ${className ?? ""}`.trim()} />;
}
