"""
Email Management Agent

Handles email composition, sending, and management operations.
"""

import asyncio
import logging
import smtplib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from core.base_agent import BaseAgent, AgentStatus
from core.message_bus import Message
from core.context_manager import ContextScope
from config.agent_config import AgentType


class EmailStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class EmailPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EmailTemplate:
    template_id: str
    name: str
    subject: str
    body: str
    variables: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Email:
    email_id: str
    sender: str
    recipients: List[str]
    subject: str
    body: str
    status: EmailStatus = EmailStatus.DRAFT
    priority: EmailPriority = EmailPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    template_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmailAgent(BaseAgent):
    """
    Email Management Agent for handling email operations.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.emails: Dict[str, Email] = {}
        self.templates: Dict[str, EmailTemplate] = {}
        self.scheduled_emails: Dict[str, asyncio.Task] = {}
        self.smtp_config: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
    async def start(self) -> bool:
        """Start the email agent and initialize email management."""
        if await super().start():
            self.logger.info("Email agent started successfully")
            # Load SMTP configuration from context
            if self.context_manager:
                self.smtp_config = self.context_manager.get("smtp_config", scope=ContextScope.GLOBAL) or {}
            # Start background task for monitoring scheduled emails
            asyncio.create_task(self._monitor_scheduled_emails())
            return True
        return False
    
    async def stop(self) -> bool:
        """Stop the email agent and cancel all scheduled emails."""
        # Cancel all scheduled emails
        for email_id, task in self.scheduled_emails.items():
            task.cancel()
        self.scheduled_emails.clear()
        
        if await super().stop():
            self.logger.info("Email agent stopped successfully")
            return True
        return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages for email management."""
        try:
            if message.data.get("action") == "compose_email":
                return await self._handle_compose_email(message)
            elif message.data.get("action") == "send_email":
                return await self._handle_send_email(message)
            elif message.data.get("action") == "schedule_email":
                return await self._handle_schedule_email(message)
            elif message.data.get("action") == "create_template":
                return await self._handle_create_template(message)
            elif message.data.get("action") == "list_emails":
                return await self._handle_list_emails(message)
            elif message.data.get("action") == "delete_email":
                return await self._handle_delete_email(message)
            else:
                return await super().process_message(message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="error_response",
                data={"error": str(e)},
                priority=message.priority
            )
    
    async def _handle_compose_email(self, message: Message) -> Message:
        """Handle email composition request."""
        email_data = message.data.get("email_data", {})
        
        # Check if using template
        template_id = email_data.get("template_id")
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            subject = template.subject
            body = template.body
            # Apply template variables
            variables = email_data.get("variables", {})
            for var_name, var_value in variables.items():
                subject = subject.replace(f"{{{{{var_name}}}}}", str(var_value))
                body = body.replace(f"{{{{{var_name}}}}}", str(var_value))
        else:
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")
        
        email = Email(
            email_id=email_data.get("email_id", f"email_{len(self.emails) + 1}"),
            sender=email_data.get("sender", ""),
            recipients=email_data.get("recipients", []),
            subject=subject,
            body=body,
            priority=EmailPriority(email_data.get("priority", "normal")),
            cc=email_data.get("cc", []),
            bcc=email_data.get("bcc", []),
            attachments=email_data.get("attachments", []),
            template_id=template_id,
            metadata=email_data.get("metadata", {})
        )
        
        self.emails[email.email_id] = email
        self.logger.info(f"Composed email: {email.email_id} - {email.subject}")
        
        return Message(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            recipient=message.sender,
            type="email_response",
            data={
                "action": "email_composed",
                "email_id": email.email_id,
                "email": self._email_to_dict(email)
            }
        )
    
    async def _handle_send_email(self, message: Message) -> Message:
        """Handle email sending request."""
        email_id = message.data.get("email_id")
        
        if email_id not in self.emails:
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={"error": f"Email {email_id} not found"}
            )
        
        email = self.emails[email_id]
        
        try:
            success = await self._send_email(email)
            if success:
                email.status = EmailStatus.SENT
                email.sent_at = datetime.now()
                self.logger.info(f"Sent email: {email_id}")
                
                return Message(
                    id=str(uuid.uuid4()),
                    sender=self.agent_id,
                    recipient=message.sender,
                    type="email_response",
                    data={
                        "action": "email_sent",
                        "email_id": email_id,
                        "sent_at": email.sent_at.isoformat()
                    }
                )
            else:
                email.status = EmailStatus.FAILED
                return Message(
                    id=str(uuid.uuid4()),
                    sender=self.agent_id,
                    recipient=message.sender,
                    type="email_response",
                    data={"error": f"Failed to send email {email_id}"}
                )
        except Exception as e:
            email.status = EmailStatus.FAILED
            self.logger.error(f"Error sending email {email_id}: {e}")
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={"error": f"Error sending email: {str(e)}"}
            )
    
    async def _handle_schedule_email(self, message: Message) -> Message:
        """Handle email scheduling request."""
        email_id = message.data.get("email_id")
        schedule_time = message.data.get("schedule_time")
        
        if email_id not in self.emails:
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={"error": f"Email {email_id} not found"}
            )
        
        if not schedule_time:
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={"error": "Schedule time is required"}
            )
        
        try:
            if isinstance(schedule_time, str):
                schedule_dt = datetime.fromisoformat(schedule_time)
            else:
                schedule_dt = schedule_time
            
            delay = (schedule_dt - datetime.now()).total_seconds()
            if delay <= 0:
                return Message(
                    id=str(uuid.uuid4()),
                    sender=self.agent_id,
                    recipient=message.sender,
                    type="email_response",
                    data={"error": "Schedule time must be in the future"}
                )
            
            # Schedule the email
            scheduled_task = asyncio.create_task(self._send_scheduled_email(email_id, delay))
            self.scheduled_emails[email_id] = scheduled_task
            
            email = self.emails[email_id]
            email.status = EmailStatus.SCHEDULED
            
            self.logger.info(f"Scheduled email {email_id} for {schedule_dt}")
            
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={
                    "action": "email_scheduled",
                    "email_id": email_id,
                    "schedule_time": schedule_dt.isoformat()
                }
            )
            
        except Exception as e:
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={"error": f"Invalid schedule time: {e}"}
            )
    
    async def _handle_create_template(self, message: Message) -> Message:
        """Handle email template creation request."""
        template_data = message.data.get("template_data", {})
        
        template = EmailTemplate(
            template_id=template_data.get("template_id", f"template_{len(self.templates) + 1}"),
            name=template_data.get("name", "Untitled Template"),
            subject=template_data.get("subject", ""),
            body=template_data.get("body", ""),
            variables=template_data.get("variables", [])
        )
        
        self.templates[template.template_id] = template
        self.logger.info(f"Created email template: {template.template_id} - {template.name}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "template_created",
                "template_id": template.template_id,
                "template": {
                    "template_id": template.template_id,
                    "name": template.name,
                    "subject": template.subject,
                    "body": template.body,
                    "variables": template.variables,
                    "created_at": template.created_at.isoformat()
                }
            }
        )
    
    async def _handle_list_emails(self, message: Message) -> Message:
        """Handle email listing request."""
        filters = message.data.get("filters", {})
        emails = self._filter_emails(filters)
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "emails_listed",
                "emails": [self._email_to_dict(email) for email in emails],
                "count": len(emails)
            }
        )
    
    async def _handle_delete_email(self, message: Message) -> Message:
        """Handle email deletion request."""
        email_id = message.data.get("email_id")
        
        if email_id not in self.emails:
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={"error": f"Email {email_id} not found"}
            )
        
        # Cancel scheduled email if exists
        if email_id in self.scheduled_emails:
            self.scheduled_emails[email_id].cancel()
            del self.scheduled_emails[email_id]
        
        del self.emails[email_id]
        self.logger.info(f"Deleted email: {email_id}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "email_deleted",
                "email_id": email_id
            }
        )
    
    async def _send_email(self, email: Email) -> bool:
        """Send an email using SMTP."""
        if not self.smtp_config:
            self.logger.error("SMTP configuration not found")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email.sender
            msg['To'] = ', '.join(email.recipients)
            msg['Subject'] = email.subject
            
            if email.cc:
                msg['Cc'] = ', '.join(email.cc)
            
            # Add body
            msg.attach(MIMEText(email.body, 'plain'))
            
            # Add attachments
            for attachment_path in email.attachments:
                try:
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment_path.split("/")[-1]}'
                    )
                    msg.attach(part)
                except Exception as e:
                    self.logger.warning(f"Failed to attach {attachment_path}: {e}")
            
            # Send email
            server = smtplib.SMTP(self.smtp_config.get("host", "localhost"), self.smtp_config.get("port", 587))
            server.starttls()
            
            if self.smtp_config.get("username") and self.smtp_config.get("password"):
                server.login(self.smtp_config["username"], self.smtp_config["password"])
            
            all_recipients = email.recipients + email.cc + email.bcc
            server.send_message(msg, from_addr=email.sender, to_addrs=all_recipients)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP error: {e}")
            return False
    
    async def _send_scheduled_email(self, email_id: str, delay: float):
        """Send a scheduled email after the specified delay."""
        try:
            await asyncio.sleep(delay)
            
            if email_id in self.emails:
                email = self.emails[email_id]
                success = await self._send_email(email)
                
                if success:
                    email.status = EmailStatus.SENT
                    email.sent_at = datetime.now()
                    self.logger.info(f"Sent scheduled email: {email_id}")
                    
                    # Notify other agents about email sent
                    await self.message_bus.broadcast(Message(
                        sender=self.agent_id,
                        data={
                            "action": "scheduled_email_sent",
                            "email_id": email_id,
                            "sent_at": email.sent_at.isoformat()
                        }
                    ))
                else:
                    email.status = EmailStatus.FAILED
                    self.logger.error(f"Failed to send scheduled email: {email_id}")
            
        except asyncio.CancelledError:
            self.logger.info(f"Scheduled email {email_id} was cancelled")
        except Exception as e:
            self.logger.error(f"Error sending scheduled email {email_id}: {e}")
            if email_id in self.emails:
                self.emails[email_id].status = EmailStatus.FAILED
    
    async def _monitor_scheduled_emails(self):
        """Monitor and clean up completed scheduled emails."""
        while self.status == AgentStatus.RUNNING:
            try:
                # Clean up completed tasks
                completed_emails = [
                    email_id for email_id, task in self.scheduled_emails.items()
                    if task.done()
                ]
                
                for email_id in completed_emails:
                    del self.scheduled_emails[email_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in scheduled email monitor: {e}")
                await asyncio.sleep(60)
    
    def _filter_emails(self, filters: Dict[str, Any]) -> List[Email]:
        """Filter emails based on criteria."""
        emails = list(self.emails.values())
        
        if "status" in filters:
            status = EmailStatus(filters["status"])
            emails = [e for e in emails if e.status == status]
        
        if "priority" in filters:
            priority = EmailPriority(filters["priority"])
            emails = [e for e in emails if e.priority == priority]
        
        if "sender" in filters:
            emails = [e for e in emails if e.sender == filters["sender"]]
        
        if "recipient" in filters:
            emails = [e for e in emails if filters["recipient"] in e.recipients]
        
        if "template_id" in filters:
            emails = [e for e in emails if e.template_id == filters["template_id"]]
        
        return emails
    
    def _email_to_dict(self, email: Email) -> Dict[str, Any]:
        """Convert email to dictionary for serialization."""
        return {
            "email_id": email.email_id,
            "sender": email.sender,
            "recipients": email.recipients,
            "subject": email.subject,
            "body": email.body,
            "status": email.status.value,
            "priority": email.priority.value,
            "created_at": email.created_at.isoformat(),
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "cc": email.cc,
            "bcc": email.bcc,
            "attachments": email.attachments,
            "template_id": email.template_id,
            "metadata": email.metadata
        }

    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for email agent."""
        try:
            action = message.data.get("action")
            
            if action == "compose_email":
                return await self._handle_compose_email(message)
            elif action == "send_email":
                return await self._handle_send_email(message)
            elif action == "compose_and_send_weather_email":
                return await self._handle_compose_and_send_weather_email(message)
            elif action == "schedule_email":
                return await self._handle_schedule_email(message)
            elif action == "create_template":
                return await self._handle_create_template(message)
            elif action == "list_emails":
                return await self._handle_list_emails(message)
            elif action == "delete_email":
                return await self._handle_delete_email(message)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error in _process_message_impl: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get email agent metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "total_emails": len(self.emails),
            "emails_by_status": {
                status.value: len([e for e in self.emails.values() if e.status == status])
                for status in EmailStatus
            },
            "emails_by_priority": {
                priority.value: len([e for e in self.emails.values() if e.priority == priority])
                for priority in EmailPriority
            },
            "scheduled_emails": len(self.scheduled_emails),
            "total_templates": len(self.templates)
        })
        return metrics
    
    async def _handle_compose_and_send_weather_email(self, message: Message) -> Message:
        """Handle compose and send weather email request from Weather Agent."""
        try:
            self.logger.info("📧 Email Agent received weather data from Weather Agent")
            
            email_data = message.data.get("email_data", {})
            
            # Compose the email
            email = Email(
                email_id=f"weather_email_{len(self.emails) + 1}",
                sender=email_data.get("sender", ""),
                recipients=email_data.get("recipients", []),
                subject=email_data.get("subject", "Weather Report"),
                body=email_data.get("body", ""),
                priority=EmailPriority(email_data.get("priority", "normal")),
                cc=email_data.get("cc", []),
                bcc=email_data.get("bcc", []),
                attachments=email_data.get("attachments", []),
                template_id=email_data.get("template_id"),
                metadata=email_data.get("metadata", {})
            )
            
            self.emails[email.email_id] = email
            self.logger.info(f"📧 Composed weather email: {email.email_id} - {email.subject}")
            
            # Send the email immediately
            success = await self._send_email(email)
            if success:
                email.status = EmailStatus.SENT
                email.sent_at = datetime.now()
                self.logger.info(f"✅ Weather email sent successfully: {email.email_id}")
                
                return Message(
                    id=str(uuid.uuid4()),
                    sender=self.agent_id,
                    recipient=message.sender,
                    type="email_response",
                    data={
                        "action": "weather_email_sent",
                        "email_id": email.email_id,
                        "email": self._email_to_dict(email)
                    }
                )
            else:
                return Message(
                    id=str(uuid.uuid4()),
                    sender=self.agent_id,
                    recipient=message.sender,
                    type="email_response",
                    data={
                        "action": "weather_email_failed",
                        "error": "Failed to send weather email"
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error handling weather email: {e}")
            return Message(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=message.sender,
                type="email_response",
                data={
                    "action": "weather_email_failed",
                    "error": str(e)
                }
            )
